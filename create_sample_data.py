import pandas as pd
import numpy as np
from pathlib import Path

def create_samples():
    # Create samples directory if it doesn't exist
    samples_dir = Path("samples")
    samples_dir.mkdir(exist_ok=True)
    
    # 1. Sales Data (CSV)
    np.random.seed(42)
    n_rows = 100
    dates = pd.date_range(start="2024-01-01", periods=n_rows, freq="D")
    categories = ["Electronique", "Vêtements", "Maison", "Jouets"]
    
    data_sales = pd.DataFrame({
        "Date": dates,
        "Produit": [f"Produit_{i%20}" for i in range(n_rows)],
        "Categorie": np.random.choice(categories, n_rows),
        "Prix_Unitaire": np.random.uniform(10, 500, n_rows).round(2),
        "Quantite": np.random.randint(1, 10, n_rows),
    })
    
    data_sales["Total"] = (data_sales["Prix_Unitaire"] * data_sales["Quantite"]).round(2)
    
    # Add some anomalies (very high prices)
    data_sales.loc[5, "Prix_Unitaire"] = 5000.00
    data_sales.loc[5, "Total"] = 5000.00 * data_sales.loc[5, "Quantite"]
    
    data_sales.loc[50, "Quantite"] = 200
    data_sales.loc[50, "Total"] = data_sales.loc[50, "Prix_Unitaire"] * 200
    
    sales_path = samples_dir / "ventes_2024.csv"
    data_sales.to_csv(sales_path, index=False, encoding="utf-8")
    print(f"[OK] Créé: {sales_path}")
    
    # 2. HR Data (Excel)
    n_staff = 50
    data_hr = pd.DataFrame({
        "ID_Employe": [f"EMP{i:03}" for i in range(1, n_staff + 1)],
        "Nom": [f"Employe_{i}" for i in range(1, n_staff + 1)],
        "Departement": np.random.choice(["RH", "IT", "Finance", "Ventes", "Marketing"], n_staff),
        "Salaire_Annuel": np.random.uniform(30000, 90000, n_staff).round(0),
        "Anciennete_Ans": np.random.randint(0, 20, n_staff),
        "Performance": np.random.uniform(1, 5, n_staff).round(1)
    })
    
    # Add anomalies (negative seniority or impossible salary)
    data_hr.loc[10, "Anciennete_Ans"] = -5
    data_hr.loc[25, "Salaire_Annuel"] = 1000000
    
    hr_path = samples_dir / "rh_donnees.xlsx"
    data_hr.to_excel(hr_path, index=False)
    print(f"[OK] Créé: {hr_path}")

if __name__ == "__main__":
    create_samples()
