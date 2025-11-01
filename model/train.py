import argparse,json,joblib,pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
FEATURES = ["OverallQual", "GrLivArea", "GarageCars", "TotalBsmtSF", "YearBuilt"]
parser=argparse.ArgumentParser()
parser.add_argument('--data',required=True)
parser.add_argument('--target',default='SalePrice')
parser.add_argument('--out',default='model/pipeline.joblib')
args=parser.parse_args()

df=pd.read_csv(args.data)
cols=FEATURES+[args.target]
df=df[cols].copy()

X=df[FEATURES]
y=df[args.target]

Xtr,Xva,ytr,yva=train_test_split(X, y, test_size=0.2, random_state=42)
"""
model = Pipeline([
    ('pre', pre),
    ('rf', RandomForestRegressor(n_estimators=300, random_state=42))
])
The final Pipeline first does all preprocessing (pre), then trains a RandomForestRegressor.
n_estimators=300: number of trees (more trees → usually better but slower).
random_state=42: makes results reproducible.
"""

model=Pipeline(steps=[
    ("imputer",SimpleImputer(strategy="median")),
    ("rf",RandomForestRegressor(n_estimators=400,random_state=42))
])
model.fit(Xtr,ytr)
mae=mean_absolute_error(yva,model.predict(Xva))
print({'MEAN ABSOLUTE ERROR':float(mae)})

joblib.dump(model,args.out)
