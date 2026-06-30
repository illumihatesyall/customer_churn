# Actionable Churn Segments

Derived from top features by mean |SHAP|. Each segment splits the customer base at the feature's median value and compares churn rates.

## Segment 1: `Contract_ord`
Customers with `Contract_ord` below 0.69 churn at **42.7%** vs 6.8% baseline — **6.32x more likely** to churn.
- mean |SHAP|: 0.6735
- group sizes: above-median n=3168, below-median n=3875
- dataset baseline churn rate: 26.54%

## Segment 2: `tenure`
Customers with `tenure` below 29.00 churn at **39.5%** vs 13.2% baseline — **2.98x more likely** to churn.
- mean |SHAP|: 0.4275
- group sizes: above-median n=3474, below-median n=3569
- dataset baseline churn rate: 26.54%

## Segment 3: `charges_per_service`
Customers with `charges_per_service` above 13.97 churn at **43.4%** vs 9.7% baseline — **4.45x more likely** to churn.
- mean |SHAP|: 0.3210
- group sizes: above-median n=3520, below-median n=3523
- dataset baseline churn rate: 26.54%
