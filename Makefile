# Random transverse-field Ising: Wolff QMC + figures.
#   make            build ./bin/rtfim_wolff_qmc
#   make figures    run sweeps + regenerate figures/
#   make clean

CXX      ?= g++
CXXFLAGS ?= -O2 -Wall
BIN       = bin

all: $(BIN)/rtfim_wolff_qmc

$(BIN)/rtfim_wolff_qmc: src/rtfim_wolff_qmc.cc | $(BIN)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BIN):
	mkdir -p $(BIN)

figures: all
	cd demo && bash run_binder_sweep.sh 0.0 40
	python3 analysis/plot_binder.py "demo/vm_L*.dat" figures/binder_crossing_pure.png 0.440687
	cd demo && bash run_binder_sweep.sh 0.2 60
	python3 analysis/plot_binder.py "demo/vm_L*.dat" figures/binder_crossing_random.png 0.443
	python3 analysis/mccoy_wu_critical_line.py figures/mccoy_wu_critical_line.png
	python3 analysis/draw_lattice.py && mv mccoy_wu_lattice.png figures/

clean:
	rm -rf $(BIN) demo/vm_*.dat

.PHONY: all figures clean
