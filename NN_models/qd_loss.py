from keras.models import Sequential
from keras.layers import Dense, Flatten, Input
import keras
import tensorflow as tf
import numpy as np

import config as cfg

lambda_ = 0.5  # lambda in loss fn
alpha_ = cfg.prediction['alpha']  # capturing (1-alpha)% of samples, for qd
alpha_lower_ = alpha_ / 2  # for pinball
alpha_upper_ = 1 - alpha_lower_
soften_ = 160.
n_ = cfg.data['batch_size']  # batch size
n_epochs_ = 1000


# define loss fn
def qd_objective(y_true, y_pred):
    """Loss_QD-soft, from algorithm 1"""
    y_true = y_true[:, 0]
    y_l = y_pred[:, 0]
    y_u = y_pred[:, 1]
    y_m = y_pred[:, 2]

    K_HU = tf.maximum(0., tf.sign(y_u - y_true))
    K_HL = tf.maximum(0., tf.sign(y_true - y_l))
    K_H = tf.multiply(K_HU, K_HL)

    K_SU = tf.sigmoid(soften_ * (y_u - y_true))
    K_SL = tf.sigmoid(soften_ * (y_true - y_l))
    K_S = tf.multiply(K_SU, K_SL)

    MPIW_c = tf.divide(tf.reduce_sum(tf.multiply((y_u - y_l), K_H)), (tf.reduce_sum(K_H)+0.001))
    # PICP_H = tf.reduce_mean(K_H)
    PICP_S = tf.reduce_mean(K_S)

    Loss_S = MPIW_c + lambda_ * n_ / (alpha_ * (1 - alpha_)) * tf.square(tf.maximum(0., (1 - alpha_) - PICP_S))

    return Loss_S


def create_qd_model(alpha):
    model = Sequential()
    model.add(Input(shape=(cfg.nn_pred['input_len'], 1)))
    model.add(Flatten())
    model.add(Dense(100, activation='relu', kernel_initializer=keras.initializers.RandomNormal(mean=0.0, stddev=0.2)))
    # model.add(Dense(100, activation='relu', kernel_initializer=keras.initializers.RandomNormal(mean=0.0, stddev=0.2)))
    # model.add(Dense(100, activation='relu'))
    # model.add(Dense(100, activation='relu'))
    model.add(Dense(3, activation='linear',
                    kernel_initializer=keras.initializers.RandomNormal(mean=0.0, stddev=0.3),
                    bias_initializer=keras.initializers.Constant(
                        value=[-2., 2., 0])))  # important to init biases to start!

    def loss_function(y_true, y_pred):
        return qd_objective(alpha, y_true, y_pred)

    # compile
    opt = keras.optimizers.Adam(lr=0.02, decay=0.01)
    model.compile(
        loss=loss_function,
        optimizer=opt)
    return model

