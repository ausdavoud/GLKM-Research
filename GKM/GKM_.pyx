# distutils: language = c++
cimport numpy as np
import numpy as np
np.import_array()
from GKM_ cimport GKM

# Define a Python class that wraps around the C++ GKM class
cdef class PyGKM:
    cdef GKM *cpp_gkm

    def __cinit__(self, np.ndarray[int, ndim=2] NN, np.ndarray[double, ndim=2]  NND, int c_true, int debug, init_labels=None):
        cdef np.ndarray[int, ndim=1] init_arr
        self.cpp_gkm = NULL

        if c_true <= 0 or c_true > NN.shape[0]:
            raise ValueError("c_true must be between 1 and NN.shape[0]")

        if init_labels is None:
            self.cpp_gkm = new GKM(NN, NND, c_true, debug)
        else:
            init_arr = np.ascontiguousarray(init_labels, dtype=np.int32)
            if init_arr.ndim != 1:
                raise ValueError("init_labels must be a 1D array")
            if init_arr.shape[0] != NN.shape[0]:
                raise ValueError("init_labels length must match NN.shape[0]")
            if np.unique(init_arr).shape[0] < c_true:
                raise ValueError("init_labels must contain at least c_true clusters")
            self.cpp_gkm = new GKM(NN, NND, c_true, debug, init_arr)

    def opt(self):
        self.cpp_gkm.opt()

    @property
    def y_pred(self):
        return np.array(self.cpp_gkm.labels)

    @property
    def loss(self):
        return np.array(self.cpp_gkm.loss) 

    @property
    def c_now(self):
        return self.cpp_gkm.c_now

    @property
    def connected(self):
        return self.cpp_gkm.connected

    def __dealloc__(self):
        if self.cpp_gkm is not NULL:
            del self.cpp_gkm
            self.cpp_gkm = NULL
