"""Generates SIMULATED smallholder-farmer data (no real people) with deliberate data-quality problems.
Run: python generate_data.py   (needs pandas, numpy). Seed fixed so results are repeatable."""
import numpy as np, pandas as pd
from datetime import date, timedelta
rng=np.random.default_rng(2026)
N=3000
counties={"Meru":["Igoji East","Igoji West","Abothuguchi"],"Tharaka-Nithi":["Chogoria","Mitheru","Gatunga"],
"Embu":["Kiambere","Mbeere North","Nthawa"],"Machakos":["Kalama","Mwala","Kathiani"],"Kitui":["Kyangwithya","Mutomo","Mwingi Central"]}
first_f=["Grace","Mary","Jane","Faith","Esther","Lucy","Mercy","Ann","Rose","Joyce","Purity","Naomi","Susan","Catherine","Beatrice"]
first_m=["John","Peter","James","Daniel","Samuel","David","Joseph","Paul","Kelvin","Brian","Moses","Isaac","Erick","Victor","Dennis"]
last=["Mwangi","Njeru","Kiprop","Mutua","Kamau","Muriuki","Wanjiru","Kinyua","Mwende","Nzioka","Kiilu","Gitonga","Mbogo","Mugambi","Kariuki","Ndung'u","Muthoni","Kimani"]
start=date(2023,1,1); end=date(2026,10,31)
def rd(a,b): return a+timedelta(days=int(rng.integers(0,(b-a).days+1)))
# champions
champ=pd.DataFrame({"champion_id":[f"VC{i:03d}" for i in range(1,31)],
 "champion_name":[f"{rng.choice(first_m+first_f)} {rng.choice(last)}" for _ in range(30)],
 "county":rng.choice(list(counties),30)})
# farmers
rows=[]
pathways=["Training only","Training + Finance","Training + Greenhouse"]
for i in range(1,N+1):
    sex=rng.choice(["F","M"],p=[0.62,0.38]); cty=rng.choice(list(counties),p=[.3,.2,.2,.15,.15])
    ch=champ[champ.county==cty].champion_id
    ch=rng.choice(ch if len(ch) else champ.champion_id)
    age=int(np.clip(rng.normal(38,11),18,75)); reg=rd(start,date(2026,9,30))
    rows.append([f"F{i:05d}",f"{rng.choice(first_f if sex=='F' else first_m)} {rng.choice(last)}",sex,age,
      "07%08d"%rng.integers(0,99999999),cty,rng.choice(counties[cty]),ch,f"Group-{rng.integers(1,121):03d}",
      reg,rng.choice(pathways,p=[.4,.4,.2]),rng.choice(["Yes","Yes","Yes","Yes","No"])])
F=pd.DataFrame(rows,columns=["farmer_id","full_name","sex","age","phone","county","ward","champion_id","group_name","registration_date","pathway","consent_to_data_use"])
# engagement model: monthly activity probability
months=pd.period_range("2023-01","2026-10",freq="M")
base={"Training only":0.45,"Training + Finance":0.62,"Training + Greenhouse":0.55}
sessions=[];att=[];sales=[];wallet=[];sid=1;tid=1;aid=1
S=[]
for m in months:
    for k in range(40):
        d=date(m.year,m.month,int(rng.integers(1,28)))
        S.append([f"S{len(S)+1:05d}",d,rng.choice(["Greenhouse basics","Vermicomposting","Water management","Savings and loans","Pest management","Record keeping"]),rng.choice(champ.champion_id)])
sess=pd.DataFrame(S,columns=["session_id","session_date","topic","champion_id"])
sess_by_month={m:sess[pd.to_datetime(sess.session_date).dt.to_period("M")==m].session_id.tolist() for m in months}
for r in F.itertuples():
    reg=pd.Period(r.registration_date,"M"); p=base[r.pathway]+(0.05 if r.sex=="F" else 0)
    alive=True
    for m in months:
        if m<reg: continue
        age_m=(m-reg).n
        p_m=p*np.exp(-0.035*age_m)+0.08
        if rng.random()<0.012*(1+age_m/24): alive=False
        if not alive: continue
        if rng.random()<p_m:
            for sidv in rng.choice(sess_by_month[m],size=int(rng.integers(1,3)),replace=False):
                att.append([f"A{aid:06d}",r.farmer_id,sidv,"Yes" if rng.random()<.92 else "No"]);aid+=1
        if rng.random()<0.12*p_m*2 and age_m>=1:
            prod=rng.choice(["Vermicompost fertiliser","Seeds","DigiShamba greenhouse"],p=([.6,.3,.1] if r.pathway!="Training + Greenhouse" else [.4,.25,.35]))
            price={"Vermicompost fertiliser":1500,"Seeds":800,"DigiShamba greenhouse":65000}[prod]
            q=int(rng.integers(1,6)) if prod!="DigiShamba greenhouse" else 1
            sales.append([f"SL{sid:06d}",r.farmer_id,date(m.year,m.month,int(rng.integers(1,28))),prod,q,price,q*price,rng.choice(["Wallet","M-Pesa","Cash"],p=[.3,.5,.2])]);sid+=1
        if r.pathway=="Training + Finance" and rng.random()<p_m*0.9:
            t=rng.choice(["Deposit","Deposit","Withdrawal","Loan disbursement","Loan repayment"])
            amt=int(rng.choice([200,500,1000,2000,5000,10000])) if t!="Loan disbursement" else int(rng.choice([10000,20000,40000]))
            wallet.append([f"W{tid:06d}",r.farmer_id,date(m.year,m.month,int(rng.integers(1,28))),t,amt]);tid+=1
A=pd.DataFrame(att,columns=["attendance_id","farmer_id","session_id","attended"])
SL=pd.DataFrame(sales,columns=["sale_id","farmer_id","sale_date","product","quantity","unit_price_kes","amount_kes","payment_method"])
W=pd.DataFrame(wallet,columns=["txn_id","farmer_id","txn_date","txn_type","amount_kes"])
# outcomes: baseline and follow-up yield survey
out=[]
for r in F.sample(1200,random_state=1).itertuples():
    b=float(rng.normal(900,200)); uplift={"Training only":1.10,"Training + Finance":1.18,"Training + Greenhouse":1.40}[r.pathway]
    acres=round(float(np.clip(rng.normal(1.5,.7),.25,5)),2)
    out.append([r.farmer_id,"2024 Long rains",acres,round(max(b,200)*acres,0),round(max(b,200)*acres*0.65*rng.uniform(.8,1.2),0)])
    if rng.random()<.8: out.append([r.farmer_id,"2025 Long rains",acres,round(max(b,200)*acres*uplift*rng.uniform(.85,1.15),0),round(max(b,200)*acres*uplift*0.65*rng.uniform(.8,1.2),0)])
O=pd.DataFrame(out,columns=["farmer_id","season","acres","harvest_kg","income_kes"])
# finance ledger: monthly sales by product (should reconcile to sales)
SL["m"]=pd.to_datetime(SL.sale_date).dt.to_period("M").astype(str)
L=SL.groupby(["m","product"],as_index=False).amount_kes.sum().rename(columns={"m":"month","amount_kes":"ledger_amount_kes"})
# ---- plant errors ----
log=[]
dup=F.sample(60,random_state=2).copy(); dup["farmer_id"]=[f"F{N+i+1:05d}" for i in range(60)]
dup["full_name"]=dup.full_name.str.upper(); F=pd.concat([F,dup],ignore_index=True); log.append(("Duplicate farmers (same person, new ID, name in capitals)",60))
idx=F.sample(130,random_state=3).index; F.loc[idx,"phone"]=np.nan; log.append(("Missing phone numbers",130))
idx=F.sample(150,random_state=4).index; F.loc[idx,"sex"]=rng.choice(["Female","female","male","Male","m","f"],150); log.append(("Inconsistent sex labels (F/M expected)",150))
idx=F.sample(90,random_state=5).index; F.loc[idx,"ward"]=F.loc[idx,"ward"].str.lower().str.replace(" ","_"); log.append(("Ward spelling variants (lower case / underscores)",90))
idx=F.sample(12,random_state=6).index; F.loc[idx,"registration_date"]=date(2027,3,1); log.append(("Registration dates in the future",12))
idx=F.sample(15,random_state=7).index; F.loc[idx,"age"]=rng.choice([5,9,150,0],15); log.append(("Impossible ages",15))
idx=SL.sample(25,random_state=8).index; SL.loc[idx,"farmer_id"]="F99999"; log.append(("Sales with farmer_id not in registry (orphans)",25))
idx=SL.sample(8,random_state=9).index; SL.loc[idx,"amount_kes"]=-abs(SL.loc[idx,"amount_kes"]); log.append(("Negative sale amounts",8))
idx=A.sample(40,random_state=10).index; A.loc[idx,"farmer_id"]="F88888"; log.append(("Attendance with unknown farmer_id",40))
SL=SL.drop(columns="m")
for mth,prod,delta in [("2025-03","Vermicompost fertiliser",-4500),("2025-08","Seeds",7200),("2026-02","DigiShamba greenhouse",-65000)]:
    L.loc[(L.month==mth)&(L["product"]==prod),"ledger_amount_kes"]+=delta
log.append(("Ledger months that do not match sales (Mar 2025, Aug 2025, Feb 2026)",3))
dd=[("farmers","farmer_id","Unique farmer ID, format Fnnnnn"),("farmers","registration_date","Date the farmer joined"),("farmers","pathway","Training only / Training + Finance / Training + Greenhouse"),
("farmers","consent_to_data_use","Yes/No consent flag"),("attendance","attended","Yes if present at session"),("sales","amount_kes","quantity x unit price in KES"),
("wallet_transactions","txn_type","Deposit, Withdrawal, Loan disbursement, Loan repayment"),("finance_ledger","ledger_amount_kes","Finance's monthly sales total by product"),
("outcomes","harvest_kg / income_kes","Farmer-reported per season")]
F.to_csv("farmers.csv",index=False); champ.to_csv("village_champions.csv",index=False); sess.to_csv("training_sessions.csv",index=False)
A.to_csv("attendance.csv",index=False); SL.to_csv("sales.csv",index=False); W.to_csv("wallet_transactions.csv",index=False)
O.to_csv("outcomes.csv",index=False); L.to_csv("finance_ledger.csv",index=False)
pd.DataFrame(dd,columns=["table","field","meaning"]).to_csv("data_dictionary_starter.csv",index=False)
pd.DataFrame(log,columns=["planted_problem","count"]).to_csv("ANSWER_KEY_planted_errors.csv",index=False)
print({n:len(x) for n,x in dict(farmers=F,champions=champ,sessions=sess,attendance=A,sales=SL,wallet=W,outcomes=O,ledger=L).items()})
