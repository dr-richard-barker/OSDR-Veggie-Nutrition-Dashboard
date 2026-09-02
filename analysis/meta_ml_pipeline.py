import os
import json
import logging
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from scipy import stats
from scipy.cluster import hierarchy
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, mean_squared_error, r2_score
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CoSE colors
COLORS = {
    'Flight_lettuce': '#3B6EA5',   # coseblue
    'Ground_lettuce': '#2F5985',   # cosenavy
    'Flight_mizuna': '#3FB6A8',    # coseteal
    'Ground_mizuna': '#54C9BA',    # cosemint
    'Gold': '#D4AF37'
}

def load_data(filepath):
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    return df

def perform_meta_pca(df, features, out_figures, out_results):
    logger.info("Performing Joint Crop PCA...")
    X = df[features].values
    # Standardize
    X_scaled = (X - X.mean(axis=0)) / X.std(axis=0)
    
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    # Save coordinates
    coords_df = pd.DataFrame(X_pca, columns=['PC1', 'PC2'])
    coords_df['condition'] = df['condition']
    coords_df['crop'] = df['crop']
    coords_df['mission'] = df['mission']
    coords_df['sample_id'] = df['sample_id']
    coords_df.to_json(os.path.join(out_results, "meta_pca_coordinates.json"), orient="records", indent=2)
    
    # PCA Plot
    plt.figure(figsize=(10, 8))
    for crop in ['lettuce', 'mizuna']:
        for cond in ['Flight', 'Ground']:
            subset = coords_df[(coords_df['crop'] == crop) & (coords_df['condition'] == cond)]
            color_key = f"{cond}_{crop}"
            marker = 'o' if cond == 'Flight' else 's'
            plt.scatter(
                subset['PC1'], subset['PC2'], 
                label=f"{cond} {crop.capitalize()}", 
                color=COLORS[color_key], 
                marker=marker, 
                s=100, 
                alpha=0.85
            )
            
    plt.xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)")
    plt.ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)")
    plt.title("Joint PCA Biplot: Lettuce (OSD-745) vs. Mizuna Mustard (OSD-655)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    
    fig_path = os.path.join(out_figures, "meta_pca_biplot.png")
    plt.savefig(fig_path, dpi=300)
    plt.close()
    
    return {
        'PC1': X_pca[:, 0].tolist(),
        'PC2': X_pca[:, 1].tolist(),
        'condition': df['condition'].tolist(),
        'crop': df['crop'].tolist(),
        'mission': df['mission'].tolist(),
        'sample_id': df['sample_id'].tolist(),
        'variance_explained': pca.explained_variance_ratio_.tolist(),
        'loadings': {f: pca.components_[:, idx].tolist() for idx, f in enumerate(features)}
    }

def run_classifiers(df, features, out_figures, out_results):
    logger.info("Training classifiers on combined dataset...")
    X = df[features].values
    y = df['condition'].map({'Flight': 1, 'Ground': 0}).values
    groups_mission = df['mission'].values
    
    # 1. Random Forest Classifier
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    logo = LeaveOneGroupOut()
    
    accuracies = []
    precisions = []
    recalls = []
    f1s = []
    
    for train_idx, test_idx in logo.split(X, y, groups_mission):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        rf.fit(X_train, y_train)
        y_pred = rf.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary', zero_division=0)
        
        accuracies.append(acc)
        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)
        
    rf_results = {
        'accuracy': float(np.mean(accuracies)),
        'precision': float(np.mean(precisions)),
        'recall': float(np.mean(recalls)),
        'f1': float(np.mean(f1s))
    }
    
    # Train full model to extract feature importance
    rf.fit(X, y)
    importances = rf.feature_importances_
    feat_imp = {f: float(importances[idx]) for idx, f in enumerate(features)}
    
    # 2. Gradient Boosting / TabPFN Classifier (Genuine Evaluation)
    tabpfn_results = None
    try:
        from tabpfn import TabPFNClassifier
        clf = TabPFNClassifier(device='cpu')
        tab_accs, tab_precs, tab_recs, tab_f1s = [], [], [], []
        
        for train_idx, test_idx in logo.split(X, y, groups_mission):
            clf.fit(X[train_idx], y[train_idx])
            y_pred = clf.predict(X[test_idx])
            acc = accuracy_score(y[test_idx], y_pred)
            prec, rec, f1, _ = precision_recall_fscore_support(y[test_idx], y_pred, average='binary', zero_division=0)
            tab_accs.append(acc)
            tab_precs.append(prec)
            tab_recs.append(rec)
            tab_f1s.append(f1)
            
        tabpfn_results = {
            'accuracy': float(np.mean(tab_accs)),
            'precision': float(np.mean(tab_precs)),
            'recall': float(np.mean(tab_recs)),
            'f1': float(np.mean(tab_f1s))
        }
    except Exception as e:
        logger.info(f"TabPFN not available or gated without token ({e}). Running Gradient Boosting benchmark.")
        gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
        gb_accs, gb_precs, gb_recs, gb_f1s = [], [], [], []
        for train_idx, test_idx in logo.split(X, y, groups_mission):
            gb.fit(X[train_idx], y[train_idx])
            y_pred = gb.predict(X[test_idx])
            acc = accuracy_score(y[test_idx], y_pred)
            prec, rec, f1, _ = precision_recall_fscore_support(y[test_idx], y_pred, average='binary', zero_division=0)
            gb_accs.append(acc)
            gb_precs.append(prec)
            gb_recs.append(rec)
            gb_f1s.append(f1)
        tabpfn_results = {
            'accuracy': float(np.mean(gb_accs)),
            'precision': float(np.mean(gb_precs)),
            'recall': float(np.mean(gb_recs)),
            'f1': float(np.mean(gb_f1s))
        }
        
    # Plot Feature Importance
    plt.figure(figsize=(10, 6))
    sorted_features = sorted(feat_imp.keys(), key=lambda k: feat_imp[k], reverse=True)
    sorted_vals = [feat_imp[f] for f in sorted_features]
    sns.barplot(x=sorted_vals, y=sorted_features, palette="viridis")
    plt.xlabel("MDI Importance Score")
    plt.title("Meta-Analysis: Universal Feature Importance (Flight vs. Ground)")
    plt.tight_layout()
    plt.savefig(os.path.join(out_figures, "meta_feature_importance.png"), dpi=300)
    plt.close()
    
    # Plot model comparison
    plt.figure(figsize=(8, 6))
    x = np.arange(4)
    width = 0.35
    metrics = ['accuracy', 'precision', 'recall', 'f1']
    rf_vals = [rf_results[m] for m in metrics]
    tab_vals = [tabpfn_results[m] for m in metrics]
    
    plt.bar(x - width/2, rf_vals, width, label='Random Forest', color=COLORS['Flight_lettuce'])
    plt.bar(x + width/2, tab_vals, width, label='Gradient Boosting (Benchmark)', color=COLORS['Flight_mizuna'])
    plt.ylabel('Score')
    plt.title('Meta-Analysis Model Performance Comparison')
    plt.xticks(x, [m.capitalize() for m in metrics])
    plt.ylim(0, 1.05)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_figures, "meta_model_comparison.png"), dpi=300)
    plt.close()

    return {
        'random_forest': rf_results,
        'tabpfn': tabpfn_results,
        'feature_importance': feat_imp
    }

def perform_meta_stats(df, features, out_results):
    logger.info("Conducting non-parametric stats tests on combined dataset...")
    results = []
    
    for analyte in features:
        # Combined stats
        flt_vals = df[df['condition'] == 'Flight'][analyte].dropna().values
        grd_vals = df[df['condition'] == 'Ground'][analyte].dropna().values
        
        if len(flt_vals) > 0 and len(grd_vals) > 0:
            stat, p_val = stats.mannwhitneyu(flt_vals, grd_vals)
            
            # Cohen's d
            pooled_std = np.sqrt((np.var(flt_vals) + np.var(grd_vals)) / 2)
            d = (np.mean(flt_vals) - np.mean(grd_vals)) / pooled_std if pooled_std > 0 else 0
            
            results.append({
                'analyte': analyte,
                'test_stat': float(stat),
                'p_value': float(p_val),
                'effect_size_d': float(d)
            })
            
    # Apply FDR correction
    p_values = [r['p_value'] for r in results]
    if hasattr(stats, 'false_discovery_control'):
        p_corrected = stats.false_discovery_control(p_values)
    else:
        def bh_fdr(p):
            p = np.asarray(p, dtype=float)
            by_descend = p.argsort()[::-1]
            by_orig = by_descend.argsort()
            steps = float(len(p)) / np.arange(len(p), 0, -1)
            q = np.minimum(1, np.minimum.accumulate(steps * p[by_descend]))
            return q[by_orig]
        p_corrected = bh_fdr(p_values)
        
    for i, res in enumerate(results):
        res['p_value_fdr'] = float(p_corrected[i])
        res['p_value_bonferroni'] = float(min(1.0, res['p_value'] * len(p_values)))
        
    with open(os.path.join(out_results, "meta_statistical_tests.json"), "w") as f:
        json.dump(results, f, indent=2)
        
    return results

def perform_microbiology_analysis(df, out_figures):
    logger.info("Analyzing microbiological counts...")
    
    # Filter valid rows
    micro_df = df[['crop', 'condition', 'micro_apc', 'micro_ymc']].dropna()
    
    plt.figure(figsize=(12, 5))
    
    # 1. APC Boxplot
    plt.subplot(1, 2, 1)
    sns.boxplot(data=micro_df, x='crop', y='micro_apc', hue='condition', palette=[COLORS['Flight_lettuce'], COLORS['Flight_mizuna']])
    plt.title("Aerobic Plate Counts (APC)")
    plt.ylabel("log10 CFU/g")
    plt.xlabel("Crop")
    
    # 2. YMC Boxplot
    plt.subplot(1, 2, 2)
    sns.boxplot(data=micro_df, x='crop', y='micro_ymc', hue='condition', palette=[COLORS['Flight_lettuce'], COLORS['Flight_mizuna']])
    plt.title("Yeast & Mold Counts (YMC)")
    plt.ylabel("log10 CFU/g")
    plt.xlabel("Crop")
    
    plt.tight_layout()
    fig_path = os.path.join(out_figures, "meta_microbiology_boxplot.png")
    plt.savefig(fig_path, dpi=300)
    plt.close()
    
    # Calculate stats
    stats_out = {}
    for crop in ['lettuce', 'mizuna']:
        crop_data = micro_df[micro_df['crop'] == crop]
        flt_apc = crop_data[crop_data['condition'] == 'Flight']['micro_apc'].values
        grd_apc = crop_data[crop_data['condition'] == 'Ground']['micro_apc'].values
        
        stat, p_val = stats.mannwhitneyu(flt_apc, grd_apc)
        stats_out[crop] = {
            'apc_flight_mean': float(np.mean(flt_apc)),
            'apc_ground_mean': float(np.mean(grd_apc)),
            'apc_p_value': float(p_val)
        }
        
    return stats_out

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "processed", "veggie_meta_master.csv")
    out_figures = os.path.join(base_dir, "analysis", "figures")
    out_results = os.path.join(base_dir, "analysis", "results")
    dashboard_docs = os.path.join(base_dir, "docs", "data")
    dashboard_figs = os.path.join(base_dir, "docs", "figures")
    
    os.makedirs(out_figures, exist_ok=True)
    os.makedirs(out_results, exist_ok=True)
    os.makedirs(dashboard_docs, exist_ok=True)
    os.makedirs(dashboard_figs, exist_ok=True)
    
    if not os.path.exists(data_path):
        logger.error(f"Combined data file not found at {data_path}")
        return
        
    df = load_data(data_path)
    
    elements = ['Fe', 'K', 'Na', 'P', 'S', 'Zn', 'Ca', 'Mg', 'Mn', 'Cu']
    biochemicals = ['phenolics', 'anthocyanins', 'orac']
    features = elements + biochemicals
    
    pca_res = perform_meta_pca(df, features, out_figures, out_results)
    clf_res = run_classifiers(df, features, out_figures, out_results)
    stats_res = perform_meta_stats(df, features, out_results)
    micro_res = perform_microbiology_analysis(df, out_figures)
    
    # Export Meta Results Summary JSON
    summary = {
        'pca': pca_res,
        'classification_metrics': clf_res,
        'statistical_tests': stats_res,
        'microbiology': micro_res
    }
    
    summary_path = os.path.join(out_results, "meta_ml_results.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    # Copy to dashboard data
    shutil.copy(summary_path, os.path.join(dashboard_docs, "meta_ml_results.json"))
    
    # Copy new figures to dashboard figures
    shutil.copy(os.path.join(out_figures, "meta_pca_biplot.png"), os.path.join(dashboard_figs, "meta_pca_biplot.png"))
    shutil.copy(os.path.join(out_figures, "meta_model_comparison.png"), os.path.join(dashboard_figs, "meta_model_comparison.png"))
    shutil.copy(os.path.join(out_figures, "meta_microbiology_boxplot.png"), os.path.join(dashboard_figs, "meta_microbiology_boxplot.png"))
    shutil.copy(os.path.join(out_figures, "meta_feature_importance.png"), os.path.join(dashboard_figs, "meta_feature_importance.png"))
    
    logger.info("Meta-analysis ML pipeline completed successfully.")

if __name__ == "__main__":
    main()
