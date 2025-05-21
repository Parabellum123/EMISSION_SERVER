import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

# === 1. Koneksi ke PostgreSQL ===
def connect_to_db():
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )
    return conn

# === 2. Ambil dan filter data ===
def load_data():
    conn = connect_to_db()
    query = """
        SELECT vessel_type, length, breadth, engine_power
        FROM vessel_data
        WHERE length IS NOT NULL AND breadth IS NOT NULL AND engine_power IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Daftar kategori
    cargo_types = [
        "Bulk carrier", "Car carrier", "Cement carrier", "Container ship", "General cargo vessel", "RO-RO"
    ]
    tanker_types = [
        "Chemical tanker", "Chemical/Oil tanker", "Crude oil tanker", "LPG carrier", "Oil tanker"
    ]

    df['category'] = df['vessel_type'].apply(
        lambda x: 'Cargo' if x in cargo_types else ('Tanker' if x in tanker_types else 'Other')
    )

    # Tambahkan x = length × breadth
    df['x'] = df['length'] * df['breadth']
    return df[df['category'].isin(['Cargo', 'Tanker'])]

# === 3. Fungsi Training & Visualisasi Model ===
def train_polynomial_model(df_category, category_name, degree=2):
    X = df_category[['x']].values
    y = df_category['engine_power'].values

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Polynomial regression
    poly = PolynomialFeatures(degree)
    X_train_poly = poly.fit_transform(X_train)
    X_test_poly = poly.transform(X_test)

    model = LinearRegression()
    model.fit(X_train_poly, y_train)
    y_pred = model.predict(X_test_poly)
    r2 = r2_score(y_test, y_pred)

    print(f"[{category_name}] R² (degree={degree}): {r2:.4f}")

    # Visualisasi
    x_range = np.linspace(X.min(), X.max(), 200).reshape(-1, 1)
    x_range_poly = poly.transform(x_range)
    y_range = model.predict(x_range_poly)

    plt.scatter(X, y, label='Data Asli')
    plt.plot(x_range, y_range, color='red', label=f'Polynomial Fit (deg={degree})')
    plt.xlabel("Length × Breadth (m²)")
    plt.ylabel("Main Engine Power (kW)")
    plt.title(f"{category_name} - Polynomial Regression (R²={r2:.3f})")
    plt.grid(True)
    plt.legend()
    plt.show()

# === 4. Main ===
def main():
    df = load_data()
    cargo_df = df[df['category'] == 'Cargo']
    tanker_df = df[df['category'] == 'Tanker']

    print(f"Total Cargo Ships: {len(cargo_df)}")
    print(f"Total Tanker Ships: {len(tanker_df)}")

    # Train & plot model for Cargo
    train_polynomial_model(cargo_df, "Cargo", degree=2)

    # Train & plot model for Tanker
    train_polynomial_model(tanker_df, "Tanker", degree=2)

if __name__ == "__main__":
    main()
