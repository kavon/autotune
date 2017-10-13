#!/usr/bin/env python
#
# Autotune flags to g++ to optimize the performance of apps/raytracer.cpp
#
# This is an extremely simplified version meant only for tutorials
#

import opentuner
from opentuner import ConfigurationManipulator
from opentuner import EnumParameter
from opentuner import IntegerParameter
from opentuner import MeasurementInterface
from opentuner import Result

import opt_data

PASSES = opt_data.OPT_PASSES


class OptFlagsTuner(MeasurementInterface):
    
  def __init__(self, *pargs, **kwargs):
    super(OptFlagsTuner, self).__init__(program_name="raytracer", *pargs,
                                        **kwargs)
    self.parallel_compile = True                                  

  def manipulator(self):
    """
    Define the search space by creating a
    ConfigurationManipulator
    """
    manipulator = ConfigurationManipulator()
    # manipulator.add_parameter(
    #   IntegerParameter('opt_level', 0, 3))
    for opt_pass in PASSES:
      manipulator.add_parameter(
        BooleanParameter(opt_pass))
    # for param, min, max in GCC_PARAMS:
    #   manipulator.add_parameter(
    #     IntegerParameter(param, min, max))
    return manipulator

  def generate_bc(self):
      cmd = ''

  def compile(self, cfg, id):
    """
    Compile a given configuration in parallel
    """
    gcc_cmd = 'g++-mp-6 apps/raytracer.cpp -o ./tmp{0}.bin'.format(id)
    gcc_cmd += ' -O{0}'.format(cfg['opt_level'])
    
    for opt_pass in PASSES:
      if cfg[flag]:
          passes += ' -{0}'.format(opt_pass)
          
      
    # for param, min, max in GCC_PARAMS:
    #   gcc_cmd += ' --param {0}={1}'.format(
    #     param, cfg[param])
    print gcc_cmd
    return self.call_program(gcc_cmd)
  
  def run_precompiled(self, desired_result, input, limit, compile_result, id):
    """
    Run a compile_result from compile() sequentially and return performance
    """
    assert compile_result['returncode'] == 0

    try:    
        run_result = self.call_program('./tmp{0}.bin'.format(id))
        assert run_result['returncode'] == 0
    finally:
        self.call_program('rm ./tmp{0}.bin'.format(id))

    return Result(time=run_result['time'])

  def compile_and_run(self, desired_result, input, limit):
    """
    Compile and run a given configuration then
    return performance
    """
    cfg = desired_result.configuration.data
    compile_result = self.compile(cfg, 0)
    return self.run_precompiled(desired_result, input, limit, compile_result, 0)

def generate_bc():
    

if __name__ == '__main__':
  argparser = opentuner.default_argparser()
  OptFlagsTuner.generate_bc()
  OptFlagsTuner.main(argparser.parse_args())
