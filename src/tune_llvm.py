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
DEBUG = False


class OptFlagsTuner(MeasurementInterface):
    
  def __init__(self, *pargs, **kwargs):
    super(OptFlagsTuner, self).__init__(program_name="raytracer", *pargs,
                                        **kwargs)
    self.parallel_compile = True
    
    # private
    phases = [
        ('simp1', opt_data.SIMPLIFY[:]),
        ('simp2', opt_data.SIMPLIFY[:]),
        ('expand1', opt_data.EXPAND[:]),
        ('expand2', opt_data.EXPAND[:])
    ]
    
    phaseMap = {}
    for name, passes in phases:
        phaseMap[name] = passes
        
    self.phases = [name for name, _ in phases]
    self.phaseMap = phaseMap

  def manipulator(self):
    """
    Define the search space by creating a
    ConfigurationManipulator
    """
    manipulator = ConfigurationManipulator()
    
    # pass groups (phases) and misc passes can be reordered relative to eachother
    allGroups = opt_data.MISC[:]
    allGroups.extend(self.phases)
    manipulator.add_parameter(PermutationParameter('phases', allGroups))
    
    # passes within each phase can be permuted
    for name in self.phases:
        manipulator.add_parameter(PermutationParameter(name, self.phaseMap[name]))
        
    # the built-in pass orderings in opt should also be considered
    # level 0 corresponds to using the passes searched for manually
    # manipulator.add_parameter(
    #   IntegerParameter('opt_level', 0, 3))
    
    return manipulator

  def build_passes(self, cfg):
    
    # opt_level = cfg['opt_level']
    # if opt_level > 0:
    #     return '-O' + str(opt_level)
      
    order = cfg['phases']
    passes = ''
    for phase in order:
      if phase in self.phaseMap:
        subOrder = cfg[phase]
        asFlags = [' -{0}'.format(p) for p in subOrder]
        passes += ''.join(asFlags)
      else:
        passes += ' -{0}'.format(phase)
    
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
    run_res = None
    opt_cmd = '(no opt cmd)'
    build_cmd = '(no build cmd)'
    try:
        # optimize
        opt_cmd = (PATH + 'opt ' + passes + ' ./src/apps/raytracer.bc -o '
                + opt_outfile)
        if DEBUG:
            print opt_cmd, '\n'
        opt_res = self.call_program(opt_cmd)
        assert opt_res['returncode'] == 0
        
        # build executable
        build_cmd = (PATH + 'clang++ ' + opt_outfile + ' -o ' + bin_outfile)
        build_res = self.call_program(build_cmd)
        assert build_res['returncode'] == 0
        
        # run
        run_res = self.call_program(bin_outfile)
        assert run_res['returncode'] == 0
    
    except:
        # ensure we made it all the way through
        print ("\n\nCRASHED IN THE FOLLOWING CONFIG:\nopt command: " + opt_cmd + "\nbuild command: " + build_cmd) 
        assert opt_res != None
        assert build_res != None
        assert run_res != None
        assert False, "Something went wrong!"
        
    finally:
        self.call_program('rm -f ' + opt_outfile + ' ' + bin_outfile)
    
    
    
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
