"""Stage 3E-3 clustering and scoring comparison utilities."""
from __future__ import annotations
import math,re
from collections import Counter
from .baselines import TfidfVectorizerLite

DOMAIN_TERMS=("教师","学生","家长","学校","课堂","课程","教学","学习","备课","作业","批改","考试","测验","评价","辅导","培训","科研","写作","教案","实验","安全","管理","人工智能","大模型","机器学习","智能体","生成","问答","推荐","识别","分析","检索","语音","图像","视频","痛点","需求","反馈","耗时","负担","效率","困难")

def hybrid_vectors(texts,char_weight=.72,word_weight=.28,max_features=6000):
    """Normalized Chinese char TF-IDF plus auditable domain-token TF-IDF."""
    char=TfidfVectorizerLite((2,4),max_features).fit_transform(texts)
    docs=[];df=Counter()
    for text in texts:
        tokens=[t for t in DOMAIN_TERMS if t.lower() in (text or '').lower()]
        tokens+=re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]{2,}",(text or '').lower())
        c=Counter(tokens);docs.append(c);df.update(c)
    vocab={t:i+max_features for i,t in enumerate(sorted(df,key=lambda x:(-df[x],x))[:800])};n=max(1,len(texts))
    out=[]
    for cv,c in zip(char,docs):
        v={i:char_weight*x for i,x in cv.items()}
        for t,count in c.items():
            if t in vocab:v[vocab[t]]=word_weight*(1+math.log(count))*(math.log((1+n)/(1+df[t]))+1)
        norm=math.sqrt(sum(x*x for x in v.values())) or 1
        out.append({i:x/norm for i,x in v.items()})
    return out

def sparse_dot(a,b):return sum(v*b.get(k,0) for k,v in a.items())

def silhouette_proxy(X,assign):
    vals=[]
    for i,a in enumerate(assign):
        same=[1-sparse_dot(X[i],X[j]) for j in range(len(X)) if i!=j and assign[j]==a]
        other=[]
        for c in set(assign)-{a}:
            ds=[1-sparse_dot(X[i],X[j]) for j in range(len(X)) if assign[j]==c]
            if ds:other.append(sum(ds)/len(ds))
        if not same or not other:vals.append(0);continue
        aa=sum(same)/len(same);bb=min(other);vals.append((bb-aa)/max(aa,bb) if max(aa,bb)>0 else 0)
    return sum(vals)/len(vals) if vals else 0

def rand_index(a,b):
    agree=total=0
    for i in range(len(a)):
        for j in range(i+1,len(a)):
            total+=1;agree+=(a[i]==a[j])==(b[i]==b[j])
    return agree/total if total else 1

def kendall_tau(order_a,order_b):
    pos={x:i for i,x in enumerate(order_b)};agree=discord=0
    for i in range(len(order_a)):
        for j in range(i+1,len(order_a)):
            agree+=(pos[order_a[i]]<pos[order_a[j]]);discord+=(pos[order_a[i]]>pos[order_a[j]])
    return (agree-discord)/(agree+discord) if agree+discord else 1

def weighted_score(dimensions,weights):
    return sum(float(dimensions[k])*weights[k] for k in weights)
