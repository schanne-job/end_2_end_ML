import pandas as pd 
import requests 

df = pd.read_csv("./kc_house_data.csv")

# choose features
features = ["bedrooms","bathrooms","sqft_living","sqft_above","grade",
            "floors","view",'sqft_lot','floors','waterfront','zipcode'] 

feature_df = df[features]
row = list(feature_df.loc[7,:])

r = requests.post("http://localhost:5000/predict", json={"data":{"ndarray":[row]}})
print(r.content)
