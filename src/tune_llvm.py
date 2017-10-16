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
from opentuner.search.objective import SearchObjective

import opt_data

# have to use one consistent clang/opt/llc build
PATH = '/Users/kavon/msr/llvm5/bin/'
DEBUG = False
OPT_LVL = '-O3'
PROG = 'tsp-ga'

# use -Xclang -disable-O0-optnone on clang to prevent it from adding optnone to everything.


class OptFlagsTuner(MeasurementInterface):
    
  def __init__(self, *pargs, **kwargs):
    super(OptFlagsTuner, self).__init__(program_name=PROG, *pargs,
                                        **kwargs)
    self.parallel_compile = True
    
    self.problem_setup = opt_data.genOptLevels()[OPT_LVL]
    phase_structure = self.problem_setup[1]
        
    self.phaseSet = set([name for name, _ in phase_structure])
    

  def manipulator(self):
    """
    Define the search space by creating a
    ConfigurationManipulator
    """
    manipulator = ConfigurationManipulator()
    
    misc_passes = self.problem_setup[2]
    phases = list(self.phaseSet)
    
    # reordering top-level phases/passes affects time
    phases.extend(misc_passes)
    manipulator.add_parameter(PermutationParameter('phases', phases))
    
    # in addition, reducing the number of top-level phases/passes can help
    manipulator.add_parameter(IntegerParameter('len_phases', 0, len(phases)))
    
    # then, passes within a phase can be permuted and/or dropped
    phase_structure = self.problem_setup[1]
    for name, passes in phase_structure:
        manipulator.add_parameter(PermutationParameter(name, passes))
        manipulator.add_parameter(IntegerParameter('len_' + name, 0, len(passes)))
    
    return manipulator

  def build_passes(self, cfg):
    passes = ' '.join(opt_data.ALWAYS_FIRST)
    
    allTopLevel = cfg['phases']
    lenTop = cfg['len_phases']
    topLevel = allTopLevel[:lenTop]
    
    for item in topLevel:
      if item in self.phaseSet:
        subOrder = cfg[item]
        subLen = cfg['len_' + item]
        asFlags = [' -{0}'.format(p) for p in subOrder[:subLen]]
        passes += ''.join(asFlags)
      else:
        passes += ' -{0}'.format(item)
    
    return passes

  def compile(self, cfg, id):
    """
    Compile a given configuration in parallel
    """
    
    passes = self.build_passes(cfg)
    
    opt_outfile = './out/' + PROG + '_opt{0}.bc'.format(id)
    bin_outfile = './out/tmp{0}.bin'.format(id)
    
    build_res = None
    opt_res = None
    run_res = None
    opt_cmd = '(no opt cmd)'
    build_cmd = '(no build cmd)'
    try:
        # optimize
        opt_cmd = (PATH + 'opt ' + passes + ' ./src/apps/' + PROG + '.bc -o '
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
    
    
    
    # apply the objective function
    objective = self.problem_setup[0]
    compile_time = opt_res['time']
    run_time = run_res['time']
    
    total_time = objective(compile_time, run_time)

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
    # outfile = 'passes_final.json'
    # print "Optimal passes written to " + outfile + ":", configuration.data
    # self.manipulator().save_to_file(configuration.data, outfile)
    msg = "Tuned on program {0}, with priority {1}. \nBest pass ordering found:\n{2}".format(
            PROG, OPT_LVL, self.build_passes(configuration.data))
    print msg
    


if __name__ == '__main__':
  argparser = opentuner.default_argparser()
  OptFlagsTuner.main(argparser.parse_args())
