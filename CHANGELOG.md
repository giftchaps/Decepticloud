# Changelog

All notable changes to the DeceptiCloud project.

## [Unreleased] - 2025-11-15

### Added

#### Core Functionality
- **Dual honeypot support**: System now supports both SSH (Cowrie) and Web (nginx) honeypots simultaneously
- **Multi-attack detection**: Enhanced state detection to monitor both SSH and web attacks independently
- **HTTP attacker simulation**: Added web traffic generator that probes common paths and simulates web attacks
- **Model persistence**: DQN agent can now save and load trained models with `agent.save()` and `agent.load()`

#### Analysis and Experimentation
- **Comprehensive data analysis notebook**: Complete Jupyter notebook with:
  - Reward trajectory visualization
  - Epsilon decay plots
  - Action distribution analysis
  - Attack detection statistics
  - Statistical comparison (t-test, Mann-Whitney U test)
  - Effect size calculation (Cohen's d)
- **Static experiment script**: `scripts/run_static_experiment.py` for running baseline control experiments
- **Enhanced CSV logging**: Per-timestep logs now include both SSH and web attack columns

#### Infrastructure
- **Improved reward function**: Multi-objective reward that incentivizes:
  - Matching honeypot type to attack type (+10)
  - Avoiding resource waste (-1 for idle honeypot)
  - Capturing attacks (-2 penalty for missed attacks)
- **Configurable log paths**: Cowrie and nginx log paths are now configurable parameters

### Changed

#### State Representation
- **Expanded from 2D to 3D state**:
  - OLD: `[attacker_detected, current_honeypot]`
  - NEW: `[ssh_attack_detected, web_attack_detected, current_honeypot]`

#### Dependencies
- **Fully pinned versions**: All dependencies now have exact version numbers for reproducibility
- **New packages**:
  - `requests==2.28.2` - For HTTP attacker simulation
  - `seaborn==0.12.2` - For enhanced visualizations
  - `scipy==1.10.1` - For statistical tests
  - `botocore==1.29.0` - AWS SDK core

#### Documentation
- **Enhanced README.md**: Added sections for:
  - Key features overview
  - State representation details
  - Action space documentation
  - Reward function specification
  - Experiment running instructions
- **Updated component descriptions**: All file descriptions now reflect new functionality

### Fixed

- **Web honeypot reward bug**: Web honeypot (action=2) now receives proper rewards when web attacks are detected
- **State detection robustness**: Added error handling for missing log files
- **Nginx log monitoring**: Fixed container log access using `docker exec` command

### Technical Improvements

- **Better error handling**: State detection gracefully handles missing logs
- **Consistent CSV format**: Both adaptive and static experiments use same output format
- **Automatic model saving**: Trained models are automatically saved to `results/dqn_model.pth`

## Known Limitations

- Static experiment results must be run separately for baseline comparison
- Cowrie container must be started at least once before logs are available
- Web attack detection relies on nginx access logs being populated

## Migration Notes

If you have existing experiment results:
- Old 2D state logs are incompatible with new 3D state representation
- Rerun experiments to generate compatible data for analysis notebook
- Old saved models cannot be loaded (state_size mismatch)
