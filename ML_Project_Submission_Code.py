# -*- coding: utf-8 -*-
"""ML_Project_Colab_Public.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_TCeW8_lqL9SFJRBCHsKV6DC3FDktIKk
"""

import pandas as pd
import collections
import numpy as np
from sklearn import set_config
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import FunctionTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score, f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

# downloading the dataset

import gdown
url = 'https://drive.google.com/uc?id=1JQ_gVoF1z57Zo2U_mDBTsOUKsWc95G2w'
data_tsv = 'data.tsv'
gdown.download(url, data_tsv, quiet=False)
data_file = 'data.tsv'

# initializing the dataframe 

import  pandas as pd
df0 = pd.read_csv(data_file, sep="\t")

df = df0.copy(deep=True)

df = df.iloc[:,1:]

df.head()

# Arrival modes '5' and '7' had very low occurences (2 each) 
# so those rows were dropped to reduce feature size

df = df[df['Arrival mode'] != 5]
df = df[df['Arrival mode'] != 7]

# Replacing NaN values in text features with empty strings

df['Diagnosis in ED'].replace(np.nan, '', inplace=True)

df.isnull().sum()

# feature-target split 

X, y = df.drop(columns=['KTAS_expert'], axis=1), df['KTAS_expert']

# train-test split

X_train, X_test, y_train, y_test = train_test_split(X, y, 
                                                    test_size=0.33, 
                                                    random_state=30)

feat_impute_0 = ['NRS_pain']                                            # features where NaN values have to be replaed with 0
feat_impute_mean = ['SBP', 'DBP', 'HR', 'RR', 'BT', 'Saturation']       # features where NaN values have to be replaed with mean
feat_onehot = ['Group', 'Sex', 'Arrival mode', 'Injury', 'Pain']        # features which have to be one-hot encoded
feat_scale_rest = ['Age', 'Patients number per hour', 'Mental']         # rest of the features which only have to be normalized

simple_imputer_0 = SimpleImputer(strategy='constant', fill_value=0)     
simple_imputer_0.fit(X[feat_impute_0])
standard_scaler_impute_0 = StandardScaler()
standard_scaler_impute_0.fit(simple_imputer_0.transform(X[feat_impute_0]))

pipe_impute_0 = Pipeline([                                              # 0 imputer and normalizing pipeline
    ('imputer', simple_imputer_0),
    ('scaler', standard_scaler_impute_0)
])

simple_imputer_mean = SimpleImputer()
simple_imputer_mean.fit(X[feat_impute_mean])
standard_scaler_impute_mean = StandardScaler()
standard_scaler_impute_mean.fit(simple_imputer_mean.transform(X[feat_impute_mean]))

pipe_impute_mean = Pipeline([                                           # mean imputer and normalizing pipeline
    ('imputer', simple_imputer_mean),
    ('scaler', standard_scaler_impute_mean)
])

count_vectorizer_complain = CountVectorizer()   
count_vectorizer_complain.fit(X['Cheif_Complain_Translated'])
lsa_complain = TruncatedSVD(n_components=120)
lsa_complain.fit(count_vectorizer_complain.transform(X['Cheif_Complain_Translated']))

pipe_complain = Pipeline([                                              # text feature vectorizer and decomposition pipeline
    ('cvec', count_vectorizer_complain),
    ('lsa', lsa_complain)
])

count_vectorizer_diagnosis = CountVectorizer()   
count_vectorizer_diagnosis.fit(X['Diagnosis in ED'])
lsa_diagnosis = TruncatedSVD(n_components=120)
lsa_diagnosis.fit(count_vectorizer_diagnosis.transform(X['Diagnosis in ED']))

pipe_diagnosis = Pipeline([                                             # text feature vectorizer and decomposition pipeline
    ('cvec', count_vectorizer_diagnosis),
    ('lsa', lsa_diagnosis)
])

one_hot_encoder =  OneHotEncoder(drop='first')                          # one-hot encoder
one_hot_encoder.fit(X[feat_onehot])

standard_scaler_rest = StandardScaler()                                 # standard normalizing saler
standard_scaler_rest.fit(X[feat_scale_rest])

pre_proc_cols = ColumnTransformer([                                     # Column transformer to conatenate the various pipelines
    ('impute_0', pipe_impute_0, feat_impute_0),
    ('impute_mean', pipe_impute_mean, feat_impute_mean),
    ('cv_complains', pipe_complain, 'Cheif_Complain_Translated'),
    ('cv_diagnosis', pipe_diagnosis, 'Diagnosis in ED'),
    ('one_hot', one_hot_encoder, feat_onehot),
    ('scale_rest', standard_scaler_rest, feat_scale_rest)
])

# Traige Accuracy metric. 

def triage_accuracy(y, y_hat):    
  tru = 0
  for tr, pr in zip(y, y_hat):
    # the accuracy window is tunable, currently set for maximizing surety in exchange for increased window size
    if (pr - tr < 1.6 and pr - tr >= 0) or (tr - pr < 1.2 and tr - pr >= 0):
      tru+=1
  return tru/len(y)

from sklearn.metrics import make_scorer

triage_score = make_scorer(triage_accuracy)

# helper function to map model's prediction to output class 

def y_class(y):
  if y < 1.4:
    return 1
  elif y < 2.4:
    return 2
  elif y < 3.4:
    return 3
  elif y < 4.4:
    return 4
  else:
    return 5

# function to map model's prediction to output class 

def triage_output(y_hat):
  y_out = [y_class(y) for y in y_hat]
  return np.array(y_out)

# a pseudo precision-recall-f1 score metric 

def triage_precision_recall_f1(y, y_hat):

  true_count_by_label = collections.Counter(y)
  
  y_out = triage_output(y_hat)
  pred_count_by_label = collections.Counter(y_out)

  correct_by_label = {
      1:0, 2:0, 3:0, 4:0, 5:0
  }

  # for tr, pr in zip(y, y_out):
  #   if tr == pr:
  #     correct_by_label[tr] += 1

  for tr, pr in zip(y, y_hat):
    if ( (tr + 0.6) > pr and (tr - 0.4) < pr ) :
      correct_by_label[tr] += 1
    elif ( (tr + 1.2) > pr and (tr - 0.8) < pr ) :
      correct_by_label[tr] += 0.4
    elif ( (tr + 1.5) > pr and (tr - 1) < pr ) :
      correct_by_label[tr] += 0.2
    elif ( pr > 5 and tr == 5 ):
      correct_by_label[5] += 1
    elif ( pr < 1 and tr == 1 ):
      correct_by_label[1] += 1

  precision = {
      1: correct_by_label[1] / pred_count_by_label[1],
      2: correct_by_label[2] / pred_count_by_label[2],
      3: correct_by_label[3] / pred_count_by_label[3],
      4: correct_by_label[4] / pred_count_by_label[4],
      5: 0,
  }

  recall = {
      1: correct_by_label[1] / true_count_by_label[1],
      2: correct_by_label[2] / true_count_by_label[2],
      3: correct_by_label[3] / true_count_by_label[3],
      4: correct_by_label[4] / true_count_by_label[4],
      5: 0,
  }

  f1 = {
      1: (2 * precision[1] * recall[1]) / (precision[1] + recall[1]),
      2: (2 * precision[2] * recall[2]) / (precision[2] + recall[2]),
      3: (2 * precision[3] * recall[3]) / (precision[3] + recall[3]),
      4: (2 * precision[4] * recall[4]) / (precision[4] + recall[4]),
      5: (2 * precision[5] * recall[5]) / (precision[5] + recall[5])
  }

  mean_val = {
      'mean precision': np.array(list(precision.values())).mean(),
      'mean recall': np.array(list(recall.values())).mean(),
      'mean f1': np.array(list(f1.values())).mean(),
  }

  return [precision, recall,  f1, mean_val]

set_config(display="diagram")

"""Training the pipeline using various regression methods."""

from sklearn.linear_model import LinearRegression

lin = LinearRegression()

pipe_lin = Pipeline([
    ('prep_proc', pre_proc_cols),
    ('clf', lin)
])

lin_params = {}

lin_grid = GridSearchCV(pipe_lin, lin_params, cv=10, scoring=triage_score)

lin_grid.fit(X_train, y_train)
y_pred = lin_grid.predict(X_test)

print('Best Score:')
print(lin_grid.best_score_)
print('Best Params:')
print(lin_grid.best_params_)
print('Accuracy on test set:')
print(triage_score(lin_grid, X_test, y_test))
prec_recall_f1 = triage_precision_recall_f1(y_test, y_pred)
print('Classwise weak precision:')
print(prec_recall_f1[0])
print('Classwise weak recall:')
print(prec_recall_f1[1])
print('Classwise weak f1-score:')
print(prec_recall_f1[2])
print('Mean weak precision:')
print(prec_recall_f1[3]['mean precision'])
print('Mean weak recall:')
print(prec_recall_f1[3]['mean recall'])
print('Mean weak f1-score:')
print(prec_recall_f1[3]['mean f1'])

# A diagram of the pipeline used in linear regression method.
# Other methos also use similar pipeline with change in the regression method used. 
pipe_lin

from sklearn.linear_model import Ridge

rig = Ridge()

pipe_rig = Pipeline([
    ('prep_proc', pre_proc_cols),
    ('clf', rig)
])

rig_params = {}
rig_params['clf__alpha'] = [0.001, 0.01, 0.1, 1.0, 10]

rig_grid = GridSearchCV(pipe_rig, rig_params, cv=10, scoring=triage_score)
rig_grid.fit(X_train, y_train)

rig_res = pd.DataFrame(rig_grid.cv_results_)[['param_clf__alpha', 'mean_test_score']]
rig_res.to_csv('ridge_params_vs_score.csv')

print('Best Score:')
print(rig_grid.best_score_)
print('Best Params:')
print(rig_grid.best_params_)
print('Accuracy on test set:')
print(triage_score(rig_grid, X_test, y_test))

y_pred = rig_grid.predict(X_test)

prec_recall_f1 = triage_precision_recall_f1(y_test, y_pred)
print('Classwise weak precision:')
print(prec_recall_f1[0])
print('Classwise weak recall:')
print(prec_recall_f1[1])
print('Classwise weak f1-score:')
print(prec_recall_f1[2])
print('Mean weak precision:')
print(prec_recall_f1[3]['mean precision'])
print('Mean weak recall:')
print(prec_recall_f1[3]['mean recall'])
print('Mean weak f1-score:')
print(prec_recall_f1[3]['mean f1'])

from sklearn.linear_model import Lasso

las = Lasso()

pipe_las = Pipeline([
    ('prep_proc', pre_proc_cols),
    ('clf', las)
])

las_params = {}
las_params['clf__alpha'] = [0.001, 0.01, 0.1, 1.0, 10]

las_grid = GridSearchCV(pipe_las, las_params, cv=10, scoring=triage_score)
las_grid.fit(X_train, y_train)

las_res = pd.DataFrame(las_grid.cv_results_)[['param_clf__alpha', 'mean_test_score']]
las_res.to_csv('lasso_params_vs_score.csv')

print('Best Score:')
print(las_grid.best_score_)
print('Best Params:')
print(las_grid.best_params_)
print('Accuracy on test set:')
print(triage_score(las_grid, X_test, y_test))

y_pred = las_grid.predict(X_test)

prec_recall_f1 = triage_precision_recall_f1(y_test, y_pred)
print('Classwise weak precision:')
print(prec_recall_f1[0])
print('Classwise weak recall:')
print(prec_recall_f1[1])
print('Classwise weak f1-score:')
print(prec_recall_f1[2])
print('Mean weak precision:')
print(prec_recall_f1[3]['mean precision'])
print('Mean weak recall:')
print(prec_recall_f1[3]['mean recall'])
print('Mean weak f1-score:')
print(prec_recall_f1[3]['mean f1'])

from sklearn.linear_model import SGDClassifier

sgd = SGDClassifier(max_iter=20000)

pipe_sgd = Pipeline([
    ('prep_proc', pre_proc_cols),
    ('clf', sgd)
])

sgd_params = {}

sgd_grid = GridSearchCV(pipe_sgd, sgd_params, cv=10, scoring=triage_score)
sgd_grid.fit(X_train, y_train)

print('Best Score:')
print(sgd_grid.best_score_)
print('Best Params:')
print(sgd_grid.best_params_)
print('Accuracy on test set:')
print(triage_score(sgd_grid, X_test, y_test))

y_pred = sgd_grid.predict(X_test)

prec_recall_f1 = triage_precision_recall_f1(y_test, y_pred)
print('Classwise weak precision:')
print(prec_recall_f1[0])
print('Classwise weak recall:')
print(prec_recall_f1[1])
print('Classwise weak f1-score:')
print(prec_recall_f1[2])
print('Mean weak precision:')
print(prec_recall_f1[3]['mean precision'])
print('Mean weak recall:')
print(prec_recall_f1[3]['mean recall'])
print('Mean weak f1-score:')
print(prec_recall_f1[3]['mean f1'])

from sklearn.svm import SVR

svr = SVR()

pipe_svr = Pipeline([
    ('prep_proc', pre_proc_cols),
    ('clf', svr)
])

svr_params = {}
svr_params['clf__kernel'] = [ 'poly', 'rbf', 'sigmoid']
svr_params['clf__C'] = [0.01, 0.1, 1.0, 10, 100]


svr_grid = GridSearchCV(pipe_svr, svr_params, cv=10, scoring=triage_score)
svr_grid.fit(X_train, y_train)

svr_res = pd.DataFrame(svr_grid.cv_results_)[['param_clf__C', 'param_clf__kernel', 'mean_test_score']]
svr_res.to_csv('SVR_params_vs_score.csv')

print('Best Score:')
print(svr_grid.best_score_)
print('Best Params:')
print(svr_grid.best_params_)
print('Accuracy on test set:')
print(triage_score(svr_grid, X_test, y_test))

y_pred = svr_grid.predict(X_test)

prec_recall_f1 = triage_precision_recall_f1(y_test, y_pred)
print('Classwise weak precision:')
print(prec_recall_f1[0])
print('Classwise weak recall:')
print(prec_recall_f1[1])
print('Classwise weak f1-score:')
print(prec_recall_f1[2])
print('Mean weak precision:')
print(prec_recall_f1[3]['mean precision'])
print('Mean weak recall:')
print(prec_recall_f1[3]['mean recall'])
print('Mean weak f1-score:')
print(prec_recall_f1[3]['mean f1'])

from sklearn.neighbors import KNeighborsRegressor

knn = KNeighborsRegressor()

pipe_knn = Pipeline([
    ('prep_proc', pre_proc_cols),
    ('clf', knn)
])

knn_params = {}
knn_params['clf__n_neighbors'] = [3, 5, 7]
knn_params['clf__weights'] = ['uniform', 'distance']

knn_grid = GridSearchCV(pipe_knn, knn_params, cv=10, scoring=triage_score)
knn_grid.fit(X_train, y_train)

knn_res = pd.DataFrame(knn_grid.cv_results_)[['param_clf__n_neighbors', 'param_clf__weights', 'mean_test_score']]
knn_res.to_csv('knn_params_vs_score.csv')

print('Best Score:')
print(knn_grid.best_score_)
print('Best Params:')
print(knn_grid.best_params_)
print('Accuracy on test set:')
print(triage_score(knn_grid, X_test, y_test))

y_pred = knn_grid.predict(X_test)

prec_recall_f1 = triage_precision_recall_f1(y_test, y_pred)
print('Classwise weak precision:')
print(prec_recall_f1[0])
print('Classwise weak recall:')
print(prec_recall_f1[1])
print('Classwise weak f1-score:')
print(prec_recall_f1[2])
print('Mean weak precision:')
print(prec_recall_f1[3]['mean precision'])
print('Mean weak recall:')
print(prec_recall_f1[3]['mean recall'])
print('Mean weak f1-score:')
print(prec_recall_f1[3]['mean f1'])

from sklearn.cross_decomposition import PLSRegression

pls = PLSRegression()

pipe_pls = Pipeline([
    ('prep_proc', pre_proc_cols),
    ('clf', pls)
])

pls_params = {}
pls_params['clf__n_components'] = [1, 2, 5, 10, 15]

pls_grid = GridSearchCV(pipe_pls, pls_params, cv=10, scoring=triage_score)

pls_grid.fit(X_train, y_train)

print('Best Score:')
print(pls_grid.best_score_)
print('Best Params:')
print(pls_grid.best_params_)
print('Accuracy on test set:')
print(triage_score(pls_grid, X_test, y_test))

y_pred = pls_grid.predict(X_test)

prec_recall_f1 = triage_precision_recall_f1(y_test, y_pred)
print('Classwise weak precision:')
print(prec_recall_f1[0])
print('Classwise weak recall:')
print(prec_recall_f1[1])
print('Classwise weak f1-score:')
print(prec_recall_f1[2])
print('Mean weak precision:')
print(prec_recall_f1[3]['mean precision'])
print('Mean weak recall:')
print(prec_recall_f1[3]['mean recall'])
print('Mean weak f1-score:')
print(prec_recall_f1[3]['mean f1'])

from sklearn.linear_model import BayesianRidge

brg = BayesianRidge()

pipe_brg = Pipeline([
    ('prep_proc', pre_proc_cols),
    ('clf', brg)
])

brg_params = {}

brg_grid = GridSearchCV(pipe_brg, brg_params, cv=10, scoring=triage_score)
brg_grid.fit(X_train, y_train)

print('Best Score:')
print(brg_grid.best_score_)
print('Best Params:')
print(brg_grid.best_params_)
print('Accuracy on test set:')
print(triage_score(brg_grid, X_test, y_test))

y_pred = brg_grid.predict(X_test)

prec_recall_f1 = triage_precision_recall_f1(y_test, y_pred)
print('Classwise weak precision:')
print(prec_recall_f1[0])
print('Classwise weak recall:')
print(prec_recall_f1[1])
print('Classwise weak f1-score:')
print(prec_recall_f1[2])
print('Mean weak precision:')
print(prec_recall_f1[3]['mean precision'])
print('Mean weak recall:')
print(prec_recall_f1[3]['mean recall'])
print('Mean weak f1-score:')
print(prec_recall_f1[3]['mean f1'])

from sklearn.tree import DecisionTreeRegressor

dtr = DecisionTreeRegressor()

pipe_dtr = Pipeline([
    ('prep_proc', pre_proc_cols),
    ('clf', dtr)
])

dtr_params = {}
dtr_params['clf__criterion'] = ['squared_error', 'friedman_mse']
dtr_params['clf__splitter'] = ['best', 'random']

dtr_grid = GridSearchCV(pipe_dtr, dtr_params, cv=10, scoring=triage_score)
dtr_grid.fit(X_train, y_train)

dtr_res = pd.DataFrame(dtr_grid.cv_results_)[['param_clf__splitter', 'param_clf__criterion', 'mean_test_score']]
dtr_res.to_csv('dtr_params_vs_score.csv')

print('Best Score:')
print(dtr_grid.best_score_)
print('Best Params:')
print(dtr_grid.best_params_)
print('Accuracy on test set:')
print(triage_score(dtr_grid, X_test, y_test))

y_pred = dtr_grid.predict(X_test)

prec_recall_f1 = triage_precision_recall_f1(y_test, y_pred)
print('Classwise weak precision:')
print(prec_recall_f1[0])
print('Classwise weak recall:')
print(prec_recall_f1[1])
print('Classwise weak f1-score:')
print(prec_recall_f1[2])
print('Mean weak precision:')
print(prec_recall_f1[3]['mean precision'])
print('Mean weak recall:')
print(prec_recall_f1[3]['mean recall'])
print('Mean weak f1-score:')
print(prec_recall_f1[3]['mean f1'])

from sklearn.ensemble import RandomForestRegressor

rft = RandomForestRegressor()

pipe_rft = Pipeline([
    ('prep_proc', pre_proc_cols),
    ('clf', rft)
])

rft_params = {}
rft_params['clf__n_estimators'] = [20, 50, 80, 100, 150, 200]
rft_params['clf__max_depth'] = [None, 3, 10, 20, 30]

rft_grid = GridSearchCV(pipe_rft, rft_params, cv=10, scoring=triage_score)
rft_grid.fit(X_train, y_train)

rft_res = pd.DataFrame(rft_grid.cv_results_)[['param_clf__n_estimators', 'param_clf__max_depth', 'mean_test_score']]
rft_res.to_csv('rft_params_vs_score.csv')

print('Best Score:')
print(rft_grid.best_score_)
print('Best Params:')
print(rft_grid.best_params_)
print('Accuracy on test set:')
print(triage_score(rft_grid, X_test, y_test))

y_pred = rft_grid.predict(X_test)

prec_recall_f1 = triage_precision_recall_f1(y_test, y_pred)
print('Classwise weak precision:')
print(prec_recall_f1[0])
print('Classwise weak recall:')
print(prec_recall_f1[1])
print('Classwise weak f1-score:')
print(prec_recall_f1[2])
print('Mean weak precision:')
print(prec_recall_f1[3]['mean precision'])
print('Mean weak recall:')
print(prec_recall_f1[3]['mean recall'])
print('Mean weak f1-score:')
print(prec_recall_f1[3]['mean f1'])

from sklearn.ensemble import AdaBoostRegressor
from sklearn.tree import DecisionTreeRegressor  # for base estimator

ada = AdaBoostRegressor()

pipe_ada = Pipeline([
    ('prep_proc', pre_proc_cols),
    ('clf', ada)
])

ada_params = {}
ada_params['clf__n_estimators'] = [50, 100, 150, 200]
ada_params['clf__base_estimator'] = [DecisionTreeRegressor(max_depth=3), 
                                     DecisionTreeRegressor(max_depth=10), 
                                     DecisionTreeRegressor(max_depth=20)]

ada_grid = GridSearchCV(pipe_ada, ada_params, cv=10, scoring=triage_score)
ada_grid.fit(X_train, y_train)

ada_res = pd.DataFrame(ada_grid.cv_results_)[['param_clf__n_estimators', 'param_clf__base_estimator', 'mean_test_score']]
ada_res.to_csv('ada_params_vs_score.csv')

print('Best Score:')
print(ada_grid.best_score_)
print('Best Params:')
print(ada_grid.best_params_)
print('Accuracy on test set:')
print(triage_score(ada_grid, X_test, y_test))

y_pred = ada_grid.predict(X_test)

prec_recall_f1 = triage_precision_recall_f1(y_test, y_pred)
print('Classwise weak precision:')
print(prec_recall_f1[0])
print('Classwise weak recall:')
print(prec_recall_f1[1])
print('Classwise weak f1-score:')
print(prec_recall_f1[2])
print('Mean weak precision:')
print(prec_recall_f1[3]['mean precision'])
print('Mean weak recall:')
print(prec_recall_f1[3]['mean recall'])
print('Mean weak f1-score:')
print(prec_recall_f1[3]['mean f1'])

from sklearn.ensemble import GradientBoostingRegressor

gdb = GradientBoostingRegressor()

pipe_gdb = Pipeline([
    ('prep_proc', pre_proc_cols),
    ('clf', gdb)
])

gdb_params = {}
gdb_params['clf__learning_rate'] = [0.01, 0.1, 1]
gdb_params['clf__n_estimators'] = [50, 100, 150, 200]

gdb_grid = GridSearchCV(pipe_gdb, gdb_params, cv=10, scoring=triage_score)
gdb_grid.fit(X_train, y_train)

gdb_res = pd.DataFrame(gdb_grid.cv_results_)[['param_clf__n_estimators', 'param_clf__learning_rate', 'mean_test_score']]
gdb_res.to_csv('gdb_params_vs_score.csv')

print('Best Score:')
print(gdb_grid.best_score_)
print('Best Params:')
print(gdb_grid.best_params_)
print('Accuracy on test set:')
print(triage_score(gdb_grid, X_test, y_test))

y_pred = gdb_grid.predict(X_test)

prec_recall_f1 = triage_precision_recall_f1(y_test, y_pred)
print('Classwise weak precision:')
print(prec_recall_f1[0])
print('Classwise weak recall:')
print(prec_recall_f1[1])
print('Classwise weak f1-score:')
print(prec_recall_f1[2])
print('Mean weak precision:')
print(prec_recall_f1[3]['mean precision'])
print('Mean weak recall:')
print(prec_recall_f1[3]['mean recall'])
print('Mean weak f1-score:')
print(prec_recall_f1[3]['mean f1'])

from sklearn.neural_network import MLPRegressor

mlp = MLPRegressor(max_iter=1000)

pipe_mlp = Pipeline([
    ('prep_proc', pre_proc_cols),
    ('clf', mlp)
])

mlp_params = {}
mlp_params['clf__hidden_layer_sizes'] = [(10,10), (20,20), (20,10,10)]

mlp_grid = GridSearchCV(pipe_mlp, mlp_params, cv=10, scoring=triage_score)
mlp_grid.fit(X_train, y_train)

mlp_res = pd.DataFrame(mlp_grid.cv_results_)[['param_clf__hidden_layer_sizes', 'mean_test_score']]
mlp_res.to_csv('mlp_params_vs_score.csv')

print('Best Score:')
print(mlp_grid.best_score_)
print('Best Params:')
print(mlp_grid.best_params_)
print('Accuracy on test set:')
print(triage_score(mlp_grid, X_test, y_test))

y_pred = mlp_grid.predict(X_test)

prec_recall_f1 = triage_precision_recall_f1(y_test, y_pred)
print('Classwise weak precision:')
print(prec_recall_f1[0])
print('Classwise weak recall:')
print(prec_recall_f1[1])
print('Classwise weak f1-score:')
print(prec_recall_f1[2])
print('Mean weak precision:')
print(prec_recall_f1[3]['mean precision'])
print('Mean weak recall:')
print(prec_recall_f1[3]['mean recall'])
print('Mean weak f1-score:')
print(prec_recall_f1[3]['mean f1'])







