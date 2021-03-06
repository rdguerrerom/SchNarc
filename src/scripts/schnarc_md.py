import sys
import os
import schnarc
import logging
import shutil
import argparse
import numpy as np
import datetime
import copy
import time
(tc, tt) = (time.process_time(), time.time())
#import schnet
import schnetpack as spk
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.utils.data.sampler import RandomSampler
sharc_path = '/user/julia/bin/py_sharc/sharc_main-py_sharc/DEVELOPMENT/pysharc/bin'
sys.path.append(sharc_path)
sys.path.append(os.path.join(sharc_path,'..','lib'))
sys.path.append(os.path.join(sharc_path,'..','lib', 'sharc'))
from sharc.pysharc.interface import SHARC_INTERFACE
import run_schnarc as rs
#import sharc and schnarc
from functools import partial
from schnarc.calculators import SchNarculator, EnsembleSchNarculator

class SHARC_NN(SHARC_INTERFACE):
    """
    Class for SHARC NN
    """
    # Name of the interface
    interface = 'NN'
    # store atom ids
    save_atids = True
    # store atom names
    save_atnames = True
    # accepted units:  0 : Bohr, 1 : Angstrom
    iunit = 0
    # not supported keys
    not_supported = ['nacdt', 'dmdr' ]

    def initial_setup(self, **kwargs):
        return

    def do_qm_job(self, tasks, Crd):
        """

        Here you should perform all your qm calculations

        depending on the tasks, that were asked
        Hamiltonian matrix and dipole moment matrix are complex
        Gradient and NACs are real
        """
        QMout = self.schnarc_init.calculate(Crd)
        return QMout

    def final_print(self):
        self.sharc_writeQMin()

    def parseTasks(self, tasks):
        """
        these things should be interface dependent

        so write what you love, it covers basically everything
        after savedir information in QMin

        """

        # find init, samestep, restart
        QMin = { key : value for key, value in self.QMin.items() }
        QMin['natom'] = self.NAtoms
        QMin['atname'] = self.AtNames
        self.n_atoms=self.NAtoms
        key_tasks = tasks['tasks'].lower().split()


        if any( [self.not_supported in key_tasks ] ):
            print( "not supported keys: ", self.not_supported )
            sys.exit(16)

        for key in key_tasks:
            QMin[key] = []

        for key in self.states:
            QMin[key] = self.states[key]


        if 'init' in QMin:
            checkscratch(QMin['savedir'])
        if not 'init' in QMin and not 'samestep' in QMin and not 'restart' in QMin:
            fromfile=os.path.join(QMin['savedir'],'U.out')
            if not os.path.isfile(fromfile):
                print( 'ERROR: savedir does not contain U.out! Maybe you need to add "init" to QM.in.' )
                sys.exit(1)
            tofile=os.path.join(QMin['savedir'],'Uold.out')
            shutil.copy(fromfile,tofile)

        for key in ['grad', 'nacdr']:
            if tasks[key].strip() != "":
                QMin[key] = []

        QMin['pwd'] = os.getcwd()

        return QMin

    def readParameter(self, param,  *args, **kwargs):

        self.NNnumber = int(1) #self.options["NNnumber"]
        # Get device
        self.device = torch.device("cuda" if param.cuda else "cpu")
        self.NAtoms = vars(self)['NAtoms']
        self.AtNames = vars(self)['AtNames']
        self.dummy_crd = np.zeros((self.NAtoms,3))
        self.hessian = True if param.hessian else False
        self.nac_approx=param.nac_approx
        self.schnarc_init = SchNarculator(self.dummy_crd,self.AtNames,param.modelpath,self.device,hessian=self.hessian,nac_approx=self.nac_approx)
        return


def main():
    """
        Main Function if program is called as standalone
    """
    parser = rs.get_parser()
    args = parser.parse_args()
    print( "Initialize: CPU time: % .3f s, wall time: %.3f s"%(time.process_time() - tc, time.time() - tt))
    adaptive = float(1.0)
    param = "schnarc_options"
    # init SHARC_NN class 
    nn = SHARC_NN()
    print( "init SHARC_NN:  CPU time: % .3f s, wall time: %.3f s"%(time.process_time() - tc, time.time() - tt))
    # run sharc dynamics
    nn.run_sharc("input",args,adaptive, initial_param=param)
    print( "run dynamics:  CPU time: % .3f s, wall time: %.3f s"%(time.process_time() - tc, time.time() - tt))
if __name__ == "__main__":
    main()



