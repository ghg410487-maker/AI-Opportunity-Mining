"""Dependency-free text baselines used by the competition MVP."""
from __future__ import annotations

import math
import random
import re
from collections import Counter

T0_LABELS = ("EDUCATION_DIRECT", "EDUCATION_WEAK", "NON_EDUCATION", "UNKNOWN")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def t0_rule_predict(text: str) -> str:
    text = normalize_text(text)
    if len(text) < 4:
        return "UNKNOWN"
    strong = (
        "教学", "学习", "课程", "作业", "考试", "测验", "备考", "辅导", "批改",
        "教务", "实训", "实验教学", "教师培训", "在线教育", "k12", "k-12",
        " tutor", "learning", "education", "student assessment",
    )
    weak = ("校园", "教师", "老师", "学生", "学校", "论文", "学术", "实验室", "培训", "知识")
    if any(k in text for k in strong):
        return "EDUCATION_DIRECT"
    if any(k in text for k in weak):
        return "EDUCATION_WEAK"
    return "NON_EDUCATION"


class TfidfVectorizerLite:
    def __init__(self, ngram_range=(2, 4), max_features=8000):
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.vocabulary_: dict[str, int] = {}
        self.idf_: list[float] = []

    def _terms(self, text):
        text = re.sub(r"\s+", "", normalize_text(text))
        out=[]
        for n in range(self.ngram_range[0], self.ngram_range[1]+1):
            out.extend(text[i:i+n] for i in range(max(0, len(text)-n+1)))
        return out

    def fit(self, texts):
        df=Counter()
        for text in texts:
            df.update(set(self._terms(text)))
        ranked=sorted(df, key=lambda x:(-df[x],x))[:self.max_features]
        self.vocabulary_={t:i for i,t in enumerate(ranked)}
        n=max(1,len(texts)); self.idf_=[math.log((1+n)/(1+df[t]))+1 for t in ranked]
        return self

    def transform(self, texts):
        rows=[]
        for text in texts:
            counts=Counter(self._terms(text)); vec={}
            for term,c in counts.items():
                i=self.vocabulary_.get(term)
                if i is not None: vec[i]=(1+math.log(c))*self.idf_[i]
            norm=math.sqrt(sum(v*v for v in vec.values())) or 1.0
            rows.append({i:v/norm for i,v in vec.items()})
        return rows

    def fit_transform(self,texts):
        return self.fit(texts).transform(texts)


def dot(w, x):
    return sum(w.get(i,0.0)*v for i,v in x.items())


class LinearOvR:
    """One-vs-rest SGD for logistic regression or linear hinge SVM."""
    def __init__(self, labels=T0_LABELS, loss="log", epochs=35, lr=.18, l2=1e-4, seed=20261114):
        self.labels=tuple(labels); self.loss=loss; self.epochs=epochs; self.lr=lr; self.l2=l2; self.seed=seed
        self.weights={}; self.bias={}

    def fit(self, X, y):
        rng=random.Random(self.seed)
        self.weights={c:{} for c in self.labels}; self.bias={c:0.0 for c in self.labels}
        order=list(range(len(X)))
        for epoch in range(self.epochs):
            rng.shuffle(order); eta=self.lr/(1+.06*epoch)
            for j in order:
                x=X[j]
                for c in self.labels:
                    target=1.0 if y[j]==c else 0.0; w=self.weights[c]; score=dot(w,x)+self.bias[c]
                    if self.loss=="log":
                        score=max(-30,min(30,score)); grad=1/(1+math.exp(-score))-target
                    else:
                        signed=1.0 if target else -1.0; grad=-signed if signed*score<1 else 0.0
                    if grad:
                        for i,v in x.items(): w[i]=w.get(i,0.0)-eta*(grad*v+self.l2*w.get(i,0.0))
                        self.bias[c]-=eta*grad
        return self

    def decision_function(self,X):
        return [{c:dot(self.weights[c],x)+self.bias[c] for c in self.labels} for x in X]

    def predict(self,X):
        return [max(s,key=s.get) for s in self.decision_function(X)]


def stratified_folds(labels, n_splits=3, seed=20261114):
    rng=random.Random(seed); by={}
    for i,y in enumerate(labels):by.setdefault(y,[]).append(i)
    folds=[[] for _ in range(n_splits)]
    for ids in by.values():
        rng.shuffle(ids)
        for j,i in enumerate(ids):folds[j%n_splits].append(i)
    return folds


def classification_metrics(y_true,y_pred,labels=T0_LABELS):
    cm={a:{b:0 for b in labels} for a in labels}
    for a,b in zip(y_true,y_pred):cm[a][b]+=1
    per={}
    for c in labels:
        tp=cm[c][c]; fp=sum(cm[a][c] for a in labels if a!=c); fn=sum(cm[c][b] for b in labels if b!=c)
        p=tp/(tp+fp) if tp+fp else 0.0; r=tp/(tp+fn) if tp+fn else 0.0
        per[c]={"support":sum(cm[c].values()),"precision":p,"recall":r,"f1":2*p*r/(p+r) if p+r else 0.0}
    return {"n":len(y_true),"accuracy":sum(a==b for a,b in zip(y_true,y_pred))/max(1,len(y_true)),"macro_f1":sum(v['f1'] for v in per.values())/len(labels),"per_class":per,"confusion_matrix":cm}


def kmeans_sparse(X,k,seed=20261114,max_iter=40):
    if not X:return []
    rng=random.Random(seed); k=max(1,min(k,len(X))); centers=[dict(X[i]) for i in rng.sample(range(len(X)),k)]
    assign=[0]*len(X)
    def dist(x,c):
        keys=set(x)|set(c); return sum((x.get(i,0)-c.get(i,0))**2 for i in keys)
    for _ in range(max_iter):
        new=[min(range(k),key=lambda j:dist(x,centers[j])) for x in X]
        if new==assign:break
        assign=new; sums=[{} for _ in range(k)]; counts=[0]*k
        for a,x in zip(assign,X):
            counts[a]+=1
            for i,v in x.items():sums[a][i]=sums[a].get(i,0)+v
        for j in range(k):
            if counts[j]:centers[j]={i:v/counts[j] for i,v in sums[j].items()}
    return assign
