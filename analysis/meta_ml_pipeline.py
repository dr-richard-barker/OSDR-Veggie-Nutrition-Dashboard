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
            'model': 'TabPFN',
            'is_tabpfn': True,
            'accuracy': float(np.mean(tab_accs)),
            'precision': float(np.mean(tab_precs)),
            'recall': float(np.mean(tab_recs)),
            'f1': float(np.mean(tab_f1s))
        }
    except Exception as e:
        logger.warning(
            "TabPFN unavailable (%s). Falling back to GradientBoostingClassifier. "
            "The result is recorded under the 'tabpfn' key for consumer "
            "compatibility but is labelled model='GradientBoostingClassifier' "
            "and is_tabpfn=False: it must not be reported as a TabPFN result.", e)
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
            # Key kept for consumer compatibility; the label is what is true.
            'model': 'GradientBoostingClassifier',
            'is_tabpfn': False,
            'fallback_reason': f'TabPFN unavailable: {e}',
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

def perform_microbiology_analysis(df, out_figures, base_dir):
    """Microbial load on edible tissue, from OSD-780.

    This replaces an analysis that read per-sample APC and YMC columns off the
    nutrient table. Those columns were not measurements: the superseded literal
    data asserted one microbial count per nutrient sample in both crops, and
    OSD-780 contains nothing of the kind.

    What OSD-780 actually is, and what constrains this analysis:

      * It covers the VEG-04 missions only. There is NO microbiology for
        lettuce (OSD-745), so no lettuce count can be reported.
      * It samples leaf, soil, root, wick, water and hardware swabs. Only leaf
        is edible tissue, and food-safety statements use leaf alone -- pooling
        soil or hardware swabs into a produce-safety number would overstate it.
      * Swab and water samples have no fresh weight and are reported per swab
        rather than per gram, so the two bases are never combined.
      * Counts span zero to ~1.7e7 CFU/g and over half the ground leaf samples
        are exactly zero, so comparisons are Mann-Whitney on raw counts and
        plots use log10(x+1). Means would be meaningless here.
    """
    logger.info("Analyzing microbiological counts (OSD-780)...")

    path = os.path.join(base_dir, "data", "processed", "microbiology_osd780.csv")
    if not os.path.exists(path):
        logger.warning("Skipping microbiology: %s not present. Run "
                       "data/fetch_osdr_data.py first.", path)
        return None

    micro = pd.read_csv(path)
    leaf = micro[micro['is_edible_tissue'] &
                 micro['cfu_per_gram_fresh_weight'].notna()].copy()
    if leaf.empty:
        logger.warning("Skipping microbiology: no leaf rows with per-gram counts.")
        return None
    leaf['log10_cfu'] = np.log10(leaf['cfu_per_gram_fresh_weight'] + 1)

    # --- figure: flight vs ground, and sanitised vs not -----------------------
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, assay in zip(axes, ['APC', 'YMC']):
        subset = leaf[leaf['assay'] == assay]
        if subset.empty:
            continue
        sns.boxplot(data=subset, x='condition', y='log10_cfu', hue='condition',
                    ax=ax, legend=False)
        sns.stripplot(data=subset, x='condition', y='log10_cfu', ax=ax,
                      color='black', size=3, alpha=0.5)
        label = 'Aerobic Plate Count' if assay == 'APC' else 'Yeast & Mould Count'
        ax.set_title(f"{label} — Tokyo Bekana leaf (OSD-780)")
        ax.set_ylabel("log10(CFU/g fresh weight + 1)")
        ax.set_xlabel("")
    plt.tight_layout()
    plt.savefig(os.path.join(out_figures, "meta_microbiology_boxplot.png"), dpi=300)
    plt.close()

    # --- statistics -----------------------------------------------------------
    out = {
        'source': 'OSD-780 (LSDS-128 plate counts)',
        'scope': ('VEG-04 Tokyo Bekana only; no microbiology exists for lettuce '
                  '(OSD-745) in the archive'),
        'tissue': 'leaf (edible tissue) only; soil, root, wick, water and '
                  'hardware swab samples excluded from food-safety comparisons',
        'unit': 'CFU per gram fresh weight',
        'n_leaf_rows': int(len(leaf)),
        'by_assay': {},
        'sample_type_counts': micro['sample_type'].value_counts().to_dict(),
    }

    for assay in sorted(leaf['assay'].unique()):
        subset = leaf[leaf['assay'] == assay]
        flight = subset[subset['condition'] == 'Flight']['cfu_per_gram_fresh_weight']
        ground = subset[subset['condition'] == 'Ground']['cfu_per_gram_fresh_weight']
        entry = {
            'n_flight': int(len(flight)), 'n_ground': int(len(ground)),
            'median_flight': float(flight.median()) if len(flight) else None,
            'median_ground': float(ground.median()) if len(ground) else None,
            'max_flight': float(flight.max()) if len(flight) else None,
            'max_ground': float(ground.max()) if len(ground) else None,
            'zero_fraction_flight': float((flight == 0).mean()) if len(flight) else None,
            'zero_fraction_ground': float((ground == 0).mean()) if len(ground) else None,
        }
        if len(flight) and len(ground):
            stat, p_val = stats.mannwhitneyu(flight, ground, alternative='two-sided')
            entry['mannwhitney_u'] = float(stat)
            entry['p_value'] = float(p_val)

        # Sanitisation, where the archive labels it.
        labelled = subset[subset['sanitisation'].isin(['clean', 'unclean'])]
        if not labelled.empty:
            clean = labelled[labelled['sanitisation'] == 'clean']['cfu_per_gram_fresh_weight']
            unclean = labelled[labelled['sanitisation'] == 'unclean']['cfu_per_gram_fresh_weight']
            san = {'n_clean': int(len(clean)), 'n_unclean': int(len(unclean)),
                   'median_clean': float(clean.median()) if len(clean) else None,
                   'median_unclean': float(unclean.median()) if len(unclean) else None}
            if len(clean) and len(unclean):
                _, p_san = stats.mannwhitneyu(clean, unclean, alternative='two-sided')
                san['p_value'] = float(p_san)
            san['conditions_labelled'] = sorted(labelled['condition'].unique())
            entry['sanitisation'] = san

            # The sanitisation labels sit on GROUND samples only; flight leaf
            # samples carry none. Comparing flight against the whole ground pool
            # therefore compares unsanitised tissue against a pool that is
            # roughly half sanitised, which would inflate the difference. The
            # defensible comparison restricts ground to the unsanitised rows.
            unclean_ground = subset[(subset['condition'] == 'Ground') &
                                    (subset['sanitisation'] == 'unclean')
                                    ]['cfu_per_gram_fresh_weight']
            if len(flight) and len(unclean_ground):
                _, p_matched = stats.mannwhitneyu(flight, unclean_ground,
                                                  alternative='two-sided')
                entry['flight_vs_unsanitised_ground'] = {
                    'note': ('Preferred comparison: flight leaf carries no '
                             'sanitisation label, so ground is restricted to '
                             'unsanitised samples.'),
                    'n_flight': int(len(flight)),
                    'n_ground_unclean': int(len(unclean_ground)),
                    'median_flight': float(flight.median()),
                    'median_ground_unclean': float(unclean_ground.median()),
                    'p_value': float(p_matched),
                }

        out['by_assay'][assay] = entry
        logger.info("  %s leaf: flight median %.1f (n=%d), ground median %.1f (n=%d)%s",
                    assay, entry['median_flight'] or 0, entry['n_flight'],
                    entry['median_ground'] or 0, entry['n_ground'],
                    f", p={entry['p_value']:.4g}" if 'p_value' in entry else "")

    return out


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
    
    # Feature set is limited to elements BOTH studies measured for EVERY sample,
    # so dropna() cannot silently shrink the cohort:
    #   - OSD-745 (lettuce) measured neither copper nor aluminium. Copper was in
    #     the superseded literal data and is not in the archive at all.
    #   - Boron is measured by both studies but is populated for only 12 of 24
    #     lettuce samples, so including it would halve the lettuce cohort. It is
    #     excluded here and remains available for single-crop analyses.
    #   - Anthocyanin was assayed for OSD-745 only, so it cannot be a cross-crop
    #     feature; it too remains available for lettuce-only analyses.
    # These nine give complete coverage: 24 lettuce + 36 Tokyo Bekana = 60 rows.
    elements = ['Fe', 'K', 'Na', 'P', 'S', 'Zn', 'Ca', 'Mg', 'Mn']
    biochemicals = ['phenolics', 'orac']
    features = elements + biochemicals

    # Real assay coverage is incomplete: the ORAC and phenolic assays did not
    # run on every sample that the ICP-OES assay covered. The superseded literal
    # dataset had no gaps because every value in it was invented, so nothing
    # downstream ever had to handle missingness.
    #
    # Rows with an incomplete feature vector are DROPPED for the multivariate
    # steps, and the drop is reported. They are not imputed: filling a gap with
    # a modelled value would put numbers back into this pipeline that no
    # instrument produced, which is the failure this repository is recovering
    # from. Per-analyte statistics further down use each analyte's own coverage
    # and are unaffected.
    complete = df.dropna(subset=features)
    dropped = len(df) - len(complete)
    if dropped:
        by_crop = (df[df[features].isna().any(axis=1)]
                   .groupby('crop').size().to_dict())
        logger.warning(
            "Multivariate steps use %d of %d rows; %d dropped for incomplete "
            "feature vectors (by crop: %s). Not imputed by design.",
            len(complete), len(df), dropped, by_crop)
    else:
        logger.info("Multivariate steps use all %d rows.", len(complete))

    pca_res = perform_meta_pca(complete, features, out_figures, out_results)
    clf_res = run_classifiers(complete, features, out_figures, out_results)
    clf_res['n_samples_used'] = int(len(complete))
    clf_res['n_samples_dropped_incomplete'] = int(dropped)
    stats_res = perform_meta_stats(df, features, out_results)
    micro_res = perform_microbiology_analysis(df, out_figures, base_dir)
    
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
