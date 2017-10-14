#!/usr/bin/env python
#
# Autotune opt passes.
#

import opentuner
from opentuner import ConfigurationManipulator
from opentuner import EnumParameter
from opentuner import IntegerParameter
from opentuner import MeasurementInterface
from opentuner import Result
from opentuner.search.manipulator import (ConfigurationManipulator,
                                          PermutationParameter)

import opt_data

# have to use one consistent clang/opt/llc build
PATH = '/Users/kavon/msr/llvm5/bin/'
PASSES = opt_data.OPT_PASSES


class OptFlagsTuner(MeasurementInterface):
    
  def __init__(self, *pargs, **kwargs):
    super(OptFlagsTuner, self).__init__(program_name="raytracer", *pargs,
                                        **kwargs)
    self.parallel_compile = True
    self.parallel_run = True
    
    # private
    self.passes_dict = {}                                

  def manipulator(self):
    """
    Define the search space by creating a
    ConfigurationManipulator
    """
    manipulator = ConfigurationManipulator()
    
    for pass_id, opt_pass in enumerate(PASSES):
      # whether to enable the pass
      manipulator.add_parameter(
        EnumParameter(opt_pass, [True, False]))
      # record the ID in the passes_dict
      self.passes_dict[pass_id] = opt_pass
    
    # also consider the order of the passes. each
    # pass has a unique ID which is its position in the PASSES list.
    manipulator.add_parameter(PermutationParameter('pass_order', range(len(PASSES))))
    
    return manipulator

  def build_passes(self, cfg):
      order = cfg['pass_order']
      passes = ''
      for pass_id in order:
        opt_pass = self.passes_dict[pass_id]
        if cfg[opt_pass]:
            passes += ' -{0}'.format(opt_pass)
      
      return passes

  def compile(self, cfg, id):
    """
    Compile a given configuration in parallel
    """
    
    passes = self.build_passes(cfg)
    
    opt_outfile = './out/raytracer_opt{0}.bc'.format(id)
    bin_outfile = './out/tmp{0}.bin'.format(id)
    
    build_res = None
    opt_res = None
    try:
        # optimize
        opt_cmd = (PATH + 'opt ' + passes + ' ./src/apps/raytracer.bc -o '
                + opt_outfile)
        print opt_cmd
        opt_res = self.call_program(opt_cmd)
        assert opt_res['returncode'] == 0
        
        # build executable
        build_cmd = (PATH + 'clang++ ' + opt_outfile + ' -o ' + bin_outfile)
        build_res = self.call_program(build_cmd)
        assert build_res['returncode'] == 0
        
        # run
        run_res = self.call_program(bin_outfile)
        assert run_res['returncode'] == 0
        
    finally:
        self.call_program('rm -f ' + opt_outfile + ' ' + bin_outfile)
    
    # ensure we made it all the way through
    assert opt_res != None
    assert build_res != None
    assert run_res != None
    
    # apply weighting
    opt_time = opt_res['time']
    run_time = run_res['time']
    
    total_time = (0.5 * opt_time) + run_time
    
    run_res['time'] = total_time
    
    return run_res

  
  def run_precompiled(self, desired_result, input, limit, compile_result, id):
    '''
    the compile_result is what is returned by compile
    '''
    
    return Result(time=compile_result['time'])

  def compile_and_run(self, desired_result, input, limit):
    """
    Compile and run a given configuration then
    return performance
    """
    cfg = desired_result.configuration.data
    compile_result = self.compile(cfg, 0)
    return self.run_precompiled(desired_result, input, limit, compile_result, 0)
    
    
  def save_final_config(self, configuration):
    """called at the end of tuning"""
    outfile = 'passes_final.json'
    print "Optimal passes written to " + outfile + ":", configuration.data
    self.manipulator().save_to_file(configuration.data, outfile)
    print "best pass ordering is:"
    print self.build_passes(configuration.data)

if __name__ == '__main__':
  argparser = opentuner.default_argparser()
  OptFlagsTuner.main(argparser.parse_args())
