from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2, f_regression, f_classif
from sklearn import preprocessing
from sklearn.feature_selection import RFE
import pandas as pd
import numpy as np 
import shap
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
#from lightgbm import LGBMClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import BaggingClassifier
from sklearn.ensemble import VotingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_selection import SelectFromModel

def ensemble2_model_resampling(n_resampling, n_estimators, featurenum, seed, x_train = None, y_train = None):
    selected_cols_dict = {}
    for x in range(n_resampling):
        sample = np.random.choice(x_train.shape[0], 200, replace = False)
        x_train_sample = x_train.iloc[sample, :]
        y_train_sample = y_train.iloc[sample]
        
        # 총 8개의 fs_method ensemble (rfe는 시간이 너무 오래 걸려서 제외)
        fs_model_tree = [RandomForestClassifier(random_state = seed, n_estimators = n_estimators),
                          ExtraTreesClassifier(random_state = seed, n_estimators = n_estimators)]

        fs_model_kb = [SelectKBest(chi2, k = 400), SelectKBest(f_classif, k = 400)]

        fs_model_shap = [RandomForestClassifier(random_state = seed, n_estimators = n_estimators)]

        # fs_model_regular = [SelectFromModel(LogisticRegression(C = 1,penalty = 'l1',solver = 'liblinear'), max_features = 800),
        #                    SelectFromModel(LogisticRegression(C = 1,penalty = 'l2',solver = 'liblinear'), max_features = 800),
        #                    SelectFromModel(LogisticRegression( penalty = 'elasticnet',solver = 'saga', l1_ratio = 0.5), max_features = 800)]

        # tree importance
        for j,fs in enumerate(fs_model_tree):
            model = fs
            model.fit(x_train_sample, y_train_sample)

            importances = model.feature_importances_
            importances_sort = np.sort(importances)
            importances_high_lst = []
            for i in range(len(importances)):
                if importances[i] > importances_sort[-400-1]:
                    importances_high_lst.append(i)
                    selected_columns = x_train.columns[importances_high_lst]

            selected_cols_dict[f'tree_importances_{j}_{x}'] = selected_columns
                  
        # select kbest
        for j, fs in enumerate(fs_model_kb):
            selector = fs
            selector.fit(x_train_sample, y_train_sample)
            selected_mask = selector.get_support()
            selected_columns = x_train.columns[selected_mask]
            selected_cols_dict[f'selectkbest_{j}_{x}'] = selected_columns

        # shap
        for j, fs in enumerate(fs_model_shap):
            model = fs
            model.fit(x_train_sample, y_train_sample)
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(x_train_sample)
            shap_values_mat = np.abs(shap_values[1])
            shap_mean = np.mean(shap_values_mat, axis = 0)
            shap_mean_sort = np.sort(shap_mean)
            importances_high_lst = []
            for i in range(len(shap_mean)):
                if shap_mean[i] > shap_mean_sort[-400-1]:
                    importances_high_lst.append(i)
            selected_columns = x_train.columns[importances_high_lst]
            selected_cols_dict[f'shap_{j}_{x}'] = selected_columns

        # # regularization
        # for j, fs in enumerate(fs_model_regular):
        #     select_model = fs
        #     select_model.fit(x_train_sample, y_train_sample)
        #     selected_mask = select_model.get_support()
        #     selected_columns = x_train.columns[selected_mask]
        #     selected_cols_dict[f'regular_{j}_{x}'] = selected_columns

    df_cols = pd.DataFrame(selected_cols_dict)

    columns = []   
    for i in df_cols.values:
        for j in i:
            columns.append(j)

    counts = dict()   # 열 별 fsmethod에 포함 된 횟수 딕셔너리 
    for col in columns:
        if col not in counts:
            counts[col] = 1
        else:
            counts[col] = counts[col] + 1

    sorted_counts = sorted(counts.items(),key = lambda x:x[1], reverse = True)
    selected_columns_lst = []
    for i in range(featurenum):    # 지정 된 featurenum 개수만큼 상위 빈출 컬럼 뽑기  
        selected_columns_lst.append(sorted_counts[i][0])
    
    return selected_columns_lst


