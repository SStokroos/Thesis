{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 2,
   "metadata": {},
   "outputs": [],
   "source": [
    "import numpy as np\n",
    "from recommender import Recommender\n",
    "from numpy.random.mtrand import RandomState\n",
    "import random\n",
    "\n",
    "class MF(Recommender):\n",
    "    def __init__(self, num_users, num_items,\n",
    "                 metric='RMSE',\n",
    "                 dim_factor=200, with_bias=False,\n",
    "                 learn_rate = 0.01, reg_factor = 0.01, reg_bias = 0.01, sd_init = 0.1,\n",
    "                 colname_user='idx_user', colname_item='idx_item',\n",
    "                 colname_outcome='outcome', colname_prediction='pred',\n",
    "                 colname_treatment='treated', colname_propensity='propensity'):\n",
    "        super().__init__(num_users=num_users, num_items=num_items,\n",
    "                         colname_user=colname_user, colname_item=colname_item,\n",
    "                         colname_outcome=colname_outcome, colname_prediction=colname_prediction,\n",
    "                         colname_treatment=colname_treatment, colname_propensity=colname_propensity)\n",
    "        self.metric = metric\n",
    "        self.dim_factor = dim_factor\n",
    "        self.rng = RandomState(seed=None)\n",
    "        self.with_bias = with_bias\n",
    "\n",
    "        self.learn_rate = learn_rate\n",
    "        self.reg_bias = reg_bias\n",
    "        self.reg_factor = reg_factor\n",
    "        self.sd_init = sd_init\n",
    "\n",
    "        self.flag_prepared = False\n",
    "\n",
    "        self.user_factors = self.rng.normal(loc=0, scale=self.sd_init, size=(self.num_users, self.dim_factor))\n",
    "        self.item_factors = self.rng.normal(loc=0, scale=self.sd_init, size=(self.num_items, self.dim_factor))\n",
    "        if self.with_bias:\n",
    "            self.user_biases = np.zeros(self.num_users)\n",
    "            self.item_biases = np.zeros(self.num_items)\n",
    "            self.global_bias = 0.0\n",
    "\n",
    "    # def prepare_dictionary(self, df, colname_time='idx_time'):\n",
    "    #     print(\"start prepare dictionary\")\n",
    "    #     self.colname_time = colname_time\n",
    "    #     self.num_times = np.max(df.loc[:, self.colname_time]) + 1\n",
    "    #     self.dict_positive_sets = dict()\n",
    "    #\n",
    "    #     df_posi = df.loc[df.loc[:, self.colname_outcome] > 0]\n",
    "    #\n",
    "    #     for t in np.arange(self.num_times):\n",
    "    #         df_t = df_posi.loc[df_posi.loc[:, self.colname_time] == t]\n",
    "    #         self.dict_positive_sets[t] = dict()\n",
    "    #         for u in np.unique(df_t.loc[:, self.colname_user]):\n",
    "    #             self.dict_positive_sets[t][u] = \\\n",
    "    #                 np.unique(df_t.loc[df_t.loc[:, self.colname_user] == u, self.colname_item].values)\n",
    "    #\n",
    "    #     self.flag_prepared = True\n",
    "    #     print(\"prepared dictionary!\")\n",
    "\n",
    "\n",
    "    def train(self, df, iter = 100):\n",
    "\n",
    "        # by default, rating prediction\n",
    "        # outcome = rating\n",
    "        df_train = df.loc[~np.isnan(df.loc[:, self.colname_outcome]), :]\n",
    "\n",
    "        # # in case of binary implicit feedback\n",
    "        # if self.metric == 'logloss':\n",
    "        #     df_train = df.loc[df.loc[:, self.colname_outcome] > 0, :]  # need only positive outcomes\n",
    "        #     if not self.flag_prepared: # prepare dictionary\n",
    "        #         self.prepare_dictionary(df)\n",
    "        # else:\n",
    "        #     df_train = df.loc[~np.isnan(df.loc[:, self.colname_outcome]), :]\n",
    "\n",
    "        err = 0\n",
    "        current_iter = 0\n",
    "        while True:\n",
    "            if self.metric == 'RMSE':\n",
    "                df_train = df_train.sample(frac=1)\n",
    "                users = df_train.loc[:, self.colname_user].values\n",
    "                items = df_train.loc[:, self.colname_item].values\n",
    "                outcomes = df_train.loc[:, self.colname_outcome].values\n",
    "\n",
    "                for n in np.arange(len(df_train)):\n",
    "                    u = users[n]\n",
    "                    i = items[n]\n",
    "                    r = outcomes[n]\n",
    "\n",
    "                    u_factor = self.user_factors[u, :]\n",
    "                    i_factor = self.item_factors[i, :]\n",
    "\n",
    "                    rating = np.sum(u_factor * i_factor)\n",
    "                    if self.with_bias:\n",
    "                        rating += self.item_biases[i] + self.user_biases[u] + self.global_bias\n",
    "\n",
    "                    coeff = r - rating\n",
    "                    err += np.abs(coeff)\n",
    "\n",
    "                    self.user_factors[u, :] += \\\n",
    "                        self.learn_rate * (coeff * i_factor - self.reg_factor * u_factor)\n",
    "                    self.item_factors[i, :] += \\\n",
    "                        self.learn_rate * (coeff * u_factor - self.reg_factor * i_factor)\n",
    "\n",
    "                    if self.with_bias:\n",
    "                        self.item_biases[i] += \\\n",
    "                            self.learn_rate * (coeff - self.reg_bias * self.item_biases[i])\n",
    "                        self.user_biases[u] += \\\n",
    "                            self.learn_rate * (coeff - self.reg_bias * self.user_biases[u])\n",
    "                        self.global_bias += \\\n",
    "                            self.learn_rate * (coeff)\n",
    "\n",
    "                    current_iter += 1\n",
    "                    if current_iter >= iter:\n",
    "                        return err / iter\n",
    "\n",
    "            elif self.metric == 'logloss': # logistic matrix factorization\n",
    "                df_train = df_train.sample(frac=1)\n",
    "                users = df_train.loc[:, self.colname_user].values\n",
    "                items = df_train.loc[:, self.colname_item].values\n",
    "                outcomes = df_train.loc[:, self.colname_outcome].values\n",
    "\n",
    "                for n in np.arange(len(df_train)):\n",
    "                    u = users[n]\n",
    "                    i = items[n]\n",
    "                    r = outcomes[n]\n",
    "\n",
    "                    u_factor = self.user_factors[u, :]\n",
    "                    i_factor = self.item_factors[i, :]\n",
    "\n",
    "                    rating = np.sum(u_factor * i_factor)\n",
    "                    if self.with_bias:\n",
    "                        rating += self.item_biases[i] + self.user_biases[u] + self.global_bias\n",
    "\n",
    "                    if r > 0:\n",
    "                        coeff = self.func_sigmoid(-rating)\n",
    "                    else:\n",
    "                        coeff = - self.func_sigmoid(rating)\n",
    "\n",
    "                    self.user_factors[u, :] += \\\n",
    "                        self.learn_rate * (coeff * i_factor - self.reg_factor * u_factor)\n",
    "                    self.item_factors[i, :] += \\\n",
    "                        self.learn_rate * (coeff * u_factor - self.reg_factor * i_factor)\n",
    "\n",
    "                    if self.with_bias:\n",
    "                        self.item_biases[i] += \\\n",
    "                            self.learn_rate * (coeff - self.reg_bias * self.item_biases[i])\n",
    "                        self.user_biases[u] += \\\n",
    "                            self.learn_rate * (coeff - self.reg_bias * self.user_biases[u])\n",
    "                        self.global_bias += \\\n",
    "                            self.learn_rate * (coeff)\n",
    "\n",
    "                    current_iter += 1\n",
    "                    if current_iter >= iter:\n",
    "                        return err / iter\n",
    "\n",
    "\n",
    "\n",
    "    def predict(self, df):\n",
    "        users = df[self.colname_user].values\n",
    "        items = df[self.colname_item].values\n",
    "        pred = np.zeros(len(df))\n",
    "        for n in np.arange(len(df)):\n",
    "            pred[n] = np.inner(self.user_factors[users[n], :], self.item_factors[items[n], :])\n",
    "            if self.with_bias:\n",
    "                pred[n] += self.item_biases[items[n]]\n",
    "                pred[n] += self.user_biases[users[n]]\n",
    "                pred[n] += self.global_bias\n",
    "\n",
    "        if self.metric == 'logloss':\n",
    "            pred = 1 / (1 + np.exp(-pred))\n",
    "        return pred"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "base",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.4"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
