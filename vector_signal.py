'''
test_point_signal - module containes classes for description test point
'''
import names_parameters as names_par
import numpy as np
class VectorValues:
    def __init__(self):
        self.storage = dict()
        self.storage.fromkeys(names_par.get_names_vector(), (0, 0))
    
    def set(self, name, ampl, phase_grad):
        '''
        name: string with name param. Valid names: Ua, Ub, Uc, Ia, Ib, Ic
        ampl: signal amplitude
        phase_grad: signal phase
        '''
        if name in names_par.get_names_vector():
            self.storage[name] = (ampl, phase_grad)

    def update(self, results):
        '''
        update values in vector
        results - tuple (Ua, phiUa), ... , (Ic, phiIc)
        '''
        for name, complex_val in zip(names_par.get_names_vector(), results):
            self.storage[name] = complex_val
    

    def get(self, name):
        '''
        get - return pair (amplitude, phase) of given name
        '''
        return self.storage[name]
    def get_ampl(self, name):
        '''
        get_ampl - return rms value signal
        '''
        return self.storage[name][0]
    def get_phase(self, name):
        '''
        get_phase - return phase signal
        '''
        return self.storage[name][1]
    

class Signal:
    '''
    Signal represents point in generator.
    '''
    def __init__(self):
        self.frequency = 0
        self.meas_result = MeasuredSignal() # dict.fromkeys(names_par.names_measured_params, 0)
        self.set_harmonics = [VectorValues()  for _ in range(0, 50)] # create 50 Harmonics
        self.set_interharmonics = [VectorValues() for _ in range(0, 49)] #create 49 interharmonics
    
    def get_main_freq_vector(self):
        '''

        '''
        return self.set_harmonics[0]

    def get_vector_harm(self, num_harm):
        '''
        Get vectror - return vector instance of harmonic from set harmonics
        where num_harm - number harmonics valid number 1 - 50, where 1 - main frequency
        '''
        return self.set_harmonics[num_harm - 1]

    def set_frequency(self, freq):
        self.frequency = freq
    
    def get_frequency(self):
        return self.frequency


    def get_vector_interharm(self, num_interharm):
        '''
        Get vector interharm - return vector instance of interharmonic
        where interharm - number interharmonic valid number 1 - 49, where 1 - first interharmonic
        '''
        return self.set_interharmonics[num_interharm - 1]

    def add(self, vector_values, freq = 50):
        '''
        add main frequency vector values
        vector_values - type VectorValues from test_point_signal.py
        '''
        # self.frequency = freq
        self.set_harmonics[0] = vector_values

    def add_harm(self, num_harm, vector_values):
        '''
        add harmonics to signal
        vvector_values - type VectorValues from test_point_signal.py
        '''
        self.set_harmonics[num_harm] = vector_values
    def add_interharm(self, num_interharm, vector_values):
        '''
        add interharmonics to signal
        vvector_values - type VectorValues from test_point_signal.py
        '''
        self.set_interharmonics[num_interharm] = vector_values

    def add_MTE_counter_harm_results(self, *args):
        '''
        Create signal from mte counter results. MTE add every phases separately
        MTE has only harmonics! no interharmonics
        args - set ziped values for each phase args[0] -> Ua, args[1] -> Ub... , args[5] ->Ic, where Ua ->((val, phase),(val_1, phase_1)....)
        '''
        Ua, Ub, Uc, Ia, Ib, Ic = args
        names = names_par.get_names_vector()
        for num_harm in range(0, 32):
            harm_val = VectorValues()
            for ind in range(len(args)):
                harm_val.set(names[ind], args[ind][0], args[ind][1])  # args[ind][0] - amplitude, args[ind][1] - phase


    def __calc_rms_value(self, name="vltg"):
        '''
        __calc_rms_value - calculate rms value voltage or current depending on the name  U = sqrt(U2^2 + U3^2 + ...) or I = sqrt ...

        valid value for name 'vltg' or 'current'
        '''
        res = []
        phase_names = names_par.get_phase_voltage_names() if name == 'vltg' else names_par.get_phase_current_names() 
        for name in phase_names:
            value = 0
            for vec_val in self.set_harmonics: #.values():
                value += vec_val.get_ampl(name) ** 2
            res.append(value ** 0.5)
        self.meas_result.update(**{nm_phase: value for nm_phase, value in zip(phase_names, res)})


    def __calc_phase_voltage(self):
        '''
        calc_phase_voltage - calc rms voltage U = sqrt(U2^2 + U3^2 + ...)
        '''
        self.__calc_rms_value(name="vltg") 


    def __calc_voltage_angles(self):
        '''
        calc angles between phases.
        '''
        nm_angles = names_par.get_measured_vltg_angle_names()
        phiB = self.set_harmonics[0].get_phase("Ub")
        phiC = self.set_harmonics[0].get_phase("Uc")
        sign = 0
        if phiB - phiC > 0:
            sign = 1
        elif phiB - phiC < 0:
            sign = -1

        angle_Uab = 0 - phiB
        angle_Ubc = phiB - phiC if np.abs(phiB - phiC) < 180 else phiB - phiC - 360 * sign
        angle_Uca = phiC

        self.meas_result.update(**{angle: val for angle, val in zip(nm_angles, (angle_Uab, angle_Ubc, angle_Uca))})

    
    def __calc_phase_current(self):
        '''
        calc_phase_current - calc rms current I = sqrt(I2^2 + I3^2 + ...)
        '''
        self.__calc_rms_value(name="current")
    
    def __calc_cosPhi(self):    #  rewrite
        '''
        calc_cos_phi - calc cos phi * (between U and I)
        '''
        angles = [self.set_harmonics[0].get_phase(name) for name in names_par.get_names_vector()]   # U_phiA, U_phiB, U_phiC, I_phiA, I_phiB, I_phiC 
        cosPhi_angles = [angles[i + 3] - angles[i] for i in range(3)]
        nm_angles = names_par.get_measured_cosPhi_names()
        self.meas_result.update(**{angle : np.cos(np.deg2rad(val)) for angle, val in zip(nm_angles, cosPhi_angles)})

    def __convert_to_complex_num(self, vec_val):
        '''
        convert_to_complex_num - convers VectorValue to complex number representation
        '''
        names = names_par.get_names_vector()
        res = np.zeros((6,1), dtype=complex)  # create vector zeros dimention 3x1
        for ind, nm in enumerate(names):
            ampl, phase = vec_val.get(nm)
            res[ind] = np.complex(ampl * np.cos(np.deg2rad(phase)), ampl * np.sin(np.deg2rad(phase)))
        return res
    
    

    def __calc_symmetrical_sequences(self):
        '''
        calc_symmetrical_seq calculates symmetrical sequences for voltage and currents
        '''
        alpha = np.complex(np.cos(2 * np.pi/3), np.sin(2 * np.pi/3))
        tranform_matrix = np.array([[1, alpha, alpha ** 2], [1, alpha ** 2, alpha], [1, 1, 1]])        
        complex_val = self.__convert_to_complex_num(self.set_harmonics[0])
        U_SYM = tranform_matrix.dot(complex_val[0 : 3]) / 3
        I_SYM = tranform_matrix.dot(complex_val[3 : ]) / 3
        # SYM = np.concatenate((U_SYM, I_SYM))
        SYM = np.absolute(np.concatenate((U_SYM, I_SYM)))
        names = names_par.get_measured_sequences_names()
        self.meas_result.update(**{seq_vltg : val[0] for seq_vltg, val in zip(names, SYM)})

    def __calc_power(self):
        '''
        calc_power - calculates active, reactive, full power
        '''

        pass

        
    def calc_linear_voltage(self, name="Uab"):
        '''
        calc_linear_voltage calcs voltage between two phases. ! Now calc only on main frequency
        name - string name between two phases. Valid names Uab, Ubc, Uca
        '''
        if name in names_par.get_linear_vltg_names():
            pass
            
        return 0

    def calc_measured_param(self):
        '''
        calc all measurement parameters from signal
        '''
        self.meas_result.set_frequency(self.frequency)
        self.__calc_phase_voltage()
        self.__calc_voltage_angles()
        self.__calc_phase_current()
        self.__calc_cosPhi()
        self.__calc_symmetrical_sequences()

    

class MeasuredSignal:
    '''
    MeasuredSignal represents result of measurement Signal. It contains set of parameters defined in names_parameters.names_measured_params
    '''
    # measured_params = names_par.names_measured_params it's for optimization
    def __init__(self):
        self.results = dict.fromkeys(names_par.names_measured_params, 0)
        self.errors = dict.fromkeys(names_par.names_measured_params, 0)
    
    def set_frequency(self, freq):
        self.results["F"] = freq

    def update(self, **kwargs):
        self.results.update(kwargs)




if __name__ == "__main__":
    pass