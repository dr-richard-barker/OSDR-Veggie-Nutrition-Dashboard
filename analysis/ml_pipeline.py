import os
import json
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import shap
import joblib
import shutil
from scipy import stats
from scipy.cluster import hierarchy
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support, mean_squared_error, r2_score
from sklearn.inspection import permutation_importance
import warnings

warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set plotting style
plt.style.use('seaborn-v0_8-whitegrid')

# CoSE colors
COLORS = {
    'Flight': '#3B6EA5',
    'Ground': '#3FB6A8',
    'Navy': '#2F5985',
    'Mint': '#54C9BA',
    'Gold': '#D4AF37'
}

def load_data(filepath):
    logging.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    return df

def perform_eda(df, out_dir):
    logging.info("Performing Exploratory Data Analysis...")
    elements = ['Fe', 'K', 'Na', 'P', 'S', 'Zn', 'Ca', 'Mg', 'Mn', 'Cu']
    biochemicals = ['phenolics', 'anthocyanins', 'orac']
    features = elements + biochemicals
    
    # 1. Correlation heatmap
    plt.figure(figsize=(10, 8))
    corr = df[features].corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", vmin=-1, vmax=1)
    plt.title("Correlation Heatmap of Nutritional Variables")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "correlation_heatmap.png"), dpi=300)
    plt.close()
    
    # 2. Violin plots: elements
    fig, axes = plt.subplots(2, 5, figsize=(15, 8))
    axes = axes.flatten()
    for i, col in enumerate(elements):
        sns.violinplot(data=df, x='condition', y=col, ax=axes[i], palette=[COLORS['Flight'], COLORS['Ground']])
        axes[i].set_title(col)
        axes[i].set_xlabel('')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "violin_elemental.png"), dpi=300)
    plt.close()
    
    # 3. Violin plots: biochemicals
    fig, axes = plt.subplots(1, 3, figsize=(12, 5))
    for i, col in enumerate(biochemicals):
        sns.violinplot(data=df, x='condition', y=col, ax=axes[i], palette=[COLORS['Flight'], COLORS['Ground']])
        axes[i].set_title(col)
        axes[i].set_xlabel('')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "violin_biochemical.png"), dpi=300)
    plt.close()
    
    # 4. Mission-level boxplots for key elements (let's pick K, Ca, Mg, Fe)
    key_elements = ['K', 'Ca', 'Mg', 'Fe']
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    for i, col in enumerate(key_elements):
        sns.boxplot(data=df, x='mission', y=col, hue='condition', ax=axes[i], palette=[COLORS['Flight'], COLORS['Ground']])
        axes[i].set_title(f"{col} across missions")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "mission_comparison.png"), dpi=300)
    plt.close()
    
    # 5. Radar chart
    # Calculate means
    radar_features = features
    means = df.groupby('condition')[radar_features].mean()
    # Normalize means to 0-1 for radar
    mins = df[radar_features].min()
    maxs = df[radar_features].max()
    norm_means = (means - mins) / (maxs - mins)
    
    angles = np.linspace(0, 2 * np.pi, len(radar_features), endpoint=False).tolist()
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    for cond in ['Flight', 'Ground']:
        if cond in norm_means.index:
            values = norm_means.loc[cond].tolist()
            values += values[:1]
            ax.plot(angles, values, label=cond, color=COLORS[cond], linewidth=2)
            ax.fill(angles, values, color=COLORS[cond], alpha=0.25)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(radar_features)
    ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    plt.title("Radar Profile: Flight vs Ground (Normalized)", pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "radar_profile.png"), dpi=300)
    plt.close()

def perform_dim_reduction(df, features, out_dir, results_dir):
    logging.info("Performing Dimensionality Reduction & Clustering...")
    X = df[features].values
    # Standardize
    X_std = (X - np.mean(X, axis=0)) / np.std(X, axis=0)
    
    pca = PCA()
    X_pca = pca.fit_transform(X_std)
    
    # Save coordinates
    coords = {
        'PC1': X_pca[:, 0].tolist(),
        'PC2': X_pca[:, 1].tolist(),
        'condition': df['condition'].tolist(),
        'mission': df['mission'].tolist(),
        'sample_id': df['sample_id'].tolist()
    }
    with open(os.path.join(results_dir, "pca_coordinates.json"), "w") as f:
        json.dump(coords, f)
        
    # Plot PCA Biplot
    plt.figure(figsize=(10, 8))
    sns.scatterplot(
        x=X_pca[:, 0], y=X_pca[:, 1], 
        hue=df['condition'], style=df['mission'], 
        palette={'Flight': COLORS['Flight'], 'Ground': COLORS['Ground']},
        s=100, alpha=0.8
    )
    plt.xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%})")
    plt.ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%})")
    plt.title("PCA Biplot")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "pca_biplot.png"), dpi=300)
    plt.close()
    
    # Plot PCA variance
    plt.figure(figsize=(8, 6))
    plt.bar(range(1, len(pca.explained_variance_ratio_) + 1), pca.explained_variance_ratio_, color=COLORS['Navy'])
    plt.xlabel("Principal Component")
    plt.ylabel("Variance Explained")
    plt.title("PCA Variance Explained")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "pca_variance.png"), dpi=300)
    plt.close()
    
    # Dendrogram
    plt.figure(figsize=(12, 6))
    Z = hierarchy.linkage(X_std, 'ward')
    labels = df['condition'].tolist()
    hierarchy.dendrogram(Z, labels=labels, leaf_rotation=90)
    plt.title("Hierarchical Clustering Dendrogram")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "dendrogram.png"), dpi=300)
    plt.close()
    
    return {
        'pca_coordinates': coords,
        'pca_loadings': pca.components_.tolist(),
        'pca_variance_explained': pca.explained_variance_ratio_.tolist()
    }

def perform_classification(df, features, out_dir, models_dir):
    logging.info("Performing Classification...")
    X = df[features]
    y = (df['condition'] == 'Flight').astype(int)
    groups = df['mission']
    
    # LOGO CV
    logo = LeaveOneGroupOut()
    
    rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    
    y_true = []
    y_pred = []
    
    for train_idx, test_idx in logo.split(X, y, groups):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        rf.fit(X_train, y_train)
        y_pred.extend(rf.predict(X_test))
        y_true.extend(y_test)
        
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary')
    cm = confusion_matrix(y_true, y_pred)
    
    # Bootstrap CI for accuracy
    n_bootstraps = 1000
    boot_accs = []
    for _ in range(n_bootstraps):
        indices = np.random.randint(0, len(y_true), len(y_true))
        y_true_boot = np.array(y_true)[indices]
        y_pred_boot = np.array(y_pred)[indices]
        boot_accs.append(accuracy_score(y_true_boot, y_pred_boot))
    ci_lower = np.percentile(boot_accs, 2.5)
    ci_upper = np.percentile(boot_accs, 97.5)
    
    # Fit on all data for feature importance and SHAP
    rf.fit(X, y)
    joblib.dump(rf, os.path.join(models_dir, "rf_classifier.joblib"))
    
    # Permutation importance
    result = permutation_importance(rf, X, y, n_repeats=10, random_state=42)
    sorted_idx = result.importances_mean.argsort()
    
    plt.figure(figsize=(10, 8))
    plt.boxplot(result.importances[sorted_idx].T, vert=False, labels=np.array(features)[sorted_idx])
    plt.title("Permutation Feature Importance (Flight vs Ground)")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "feature_importance.png"), dpi=300)
    plt.close()
    
    # SHAP
    shap_values_dict = {}
    try:
        explainer = shap.TreeExplainer(rf)
        shap_values = explainer.shap_values(X)
        if isinstance(shap_values, list):
            sv = shap_values[1] # positive class (Flight)
        else:
            sv = shap_values
            
        plt.figure()
        shap.summary_plot(sv, X, show=False)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "shap_summary.png"), dpi=300)
        plt.close()
        
        plt.figure()
        shap.summary_plot(sv, X, plot_type="bar", show=False)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "shap_bar.png"), dpi=300)
        plt.close()
        
        shap_values_dict = {
            'features': features,
            'mean_abs_shap': np.abs(sv).mean(axis=0).tolist()
        }
    except Exception as e:
        logging.warning(f"SHAP failed: {e}")
        
    # Confusion Matrix Plot
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Ground', 'Flight'], yticklabels=['Ground', 'Flight'])
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "confusion_matrix.png"), dpi=300)
    plt.close()
    
    return {
        'accuracy': float(acc),
        'accuracy_ci': [float(ci_lower), float(ci_upper)],
        'precision': float(prec),
        'recall': float(rec),
        'f1': float(f1),
        'confusion_matrix': cm.tolist(),
        'feature_importance_permutation': {
            'features': np.array(features)[sorted_idx].tolist(),
            'importances_mean': result.importances_mean[sorted_idx].tolist()
        },
        'shap_values': shap_values_dict
    }

def perform_regression(df, elements, biochemicals, out_dir):
    logging.info("Performing Regression...")
    metrics = {}
    
    for target in biochemicals:
        df_clean = df.dropna(subset=elements + [target])
        if len(df_clean) == 0:
            continue
            
        X = df_clean[elements]
        y = df_clean[target]
        
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X, y)
        y_pred = rf.predict(X)
        
        r2 = r2_score(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        
        metrics[target] = {
            'R2': float(r2),
            'RMSE': float(rmse)
        }
        
        try:
            explainer = shap.TreeExplainer(rf)
            shap_values = explainer.shap_values(X)
            
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            top3_idx = mean_abs_shap.argsort()[-3:][::-1]
            top3_features = np.array(elements)[top3_idx]
            
            for feat in top3_features:
                plt.figure()
                shap.dependence_plot(feat, shap_values, X, show=False)
                plt.tight_layout()
                plt.savefig(os.path.join(out_dir, f"shap_dependence_{target}_{feat}.png"), dpi=300)
                plt.close()
        except Exception as e:
            logging.warning(f"SHAP regression failed for {target}: {e}")
            
    return metrics

def perform_stats(df, features, results_dir):
    logging.info("Performing Statistical Testing...")
    flight = df[df['condition'] == 'Flight']
    ground = df[df['condition'] == 'Ground']
    
    results = []
    p_values = []
    
    for feat in features:
        f_vals = flight[feat].dropna().values
        g_vals = ground[feat].dropna().values
        
        if len(f_vals) > 0 and len(g_vals) > 0:
            stat, p = stats.mannwhitneyu(f_vals, g_vals, alternative='two-sided')
            p_values.append(p)
            
            n1, n2 = len(f_vals), len(g_vals)
            var1, var2 = np.var(f_vals, ddof=1), np.var(g_vals, ddof=1)
            pooled_sd = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
            d = (np.mean(f_vals) - np.mean(g_vals)) / pooled_sd if pooled_sd > 0 else 0
            
            results.append({
                'analyte': feat,
                'test_stat': float(stat),
                'p_value': float(p),
                'effect_size_d': float(d)
            })
            
    if hasattr(stats, 'false_discovery_control'):
        p_corrected = stats.false_discovery_control(p_values)
    else:
        def bh_fdr(p):
            p = np.asfarray(p)
            by_descend = p.argsort()[::-1]
            by_orig = by_descend.argsort()
            steps = float(len(p)) / np.arange(len(p), 0, -1)
            q = np.minimum(1, np.minimum.accumulate(steps * p[by_descend]))
            return q[by_orig]
        p_corrected = bh_fdr(p_values)
        
    for i, res in enumerate(results):
        res['p_value_fdr'] = float(p_corrected[i])
        res['p_value_bonferroni'] = float(min(1.0, res['p_value'] * len(p_values)))
        
    with open(os.path.join(results_dir, "statistical_tests.json"), "w") as f:
        json.dump(results, f, indent=2)
        
    return results

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "processed", "veggie_nutrition_master.csv")
    out_figures = os.path.join(base_dir, "analysis", "figures")
    out_results = os.path.join(base_dir, "analysis", "results")
    out_models = os.path.join(base_dir, "analysis", "models")
    dashboard_docs = os.path.join(base_dir, "docs", "data")
    
    # Ensure directories exist
    os.makedirs(out_figures, exist_ok=True)
    os.makedirs(out_results, exist_ok=True)
    os.makedirs(out_models, exist_ok=True)
    os.makedirs(dashboard_docs, exist_ok=True)
    
    if not os.path.exists(data_path):
        logging.warning(f"Data file not found at {data_path}. Please ensure data/processed/veggie_nutrition_master.csv is present.")
        return
        
    df = load_data(data_path)
    
    elements = ['Fe', 'K', 'Na', 'P', 'S', 'Zn', 'Ca', 'Mg', 'Mn', 'Cu']
    biochemicals = ['phenolics', 'anthocyanins', 'orac']
    features = elements + biochemicals
    
    perform_eda(df, out_figures)
    dim_results = perform_dim_reduction(df, features, out_figures, out_results)
    clf_results = perform_classification(df, features, out_figures, out_models)
    reg_results = perform_regression(df, elements, biochemicals, out_figures)
    stats_results = perform_stats(df, features, out_results)
    
    logging.info("Exporting Summary for Dashboard...")
    summary = {
        'pca': dim_results,
        'classification_metrics': clf_results,
        'regression_metrics': reg_results,
        'statistical_tests': stats_results
    }
    
    summary_path = os.path.join(out_results, "ml_results_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    shutil.copy(summary_path, os.path.join(dashboard_docs, "ml_results.json"))
    logging.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
