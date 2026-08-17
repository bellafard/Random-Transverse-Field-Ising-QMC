/*
 * ============================================================================
 *  Wolff cluster quantum Monte Carlo for the
 *  random transverse-field Ising chain (RTFIM)
 * ============================================================================
 *
 *  Author: Arash Bellafard (UCLA).  Clean, from-scratch reimplementation of the
 *  production research code, specialized to the single-color (Ising) case.
 *
 *  Physics
 *  -------
 *  The quantum Hamiltonian is the 1D random transverse-field Ising chain
 *
 *      H = - sum_i J_i sigma^z_i sigma^z_{i+1}  -  sum_i h_i sigma^x_i ,
 *
 *  with random, positive couplings J_i.  Its imaginary-time path integral maps
 *  onto a (1+1)-dimensional *classical* Ising model on an L x Ltau lattice whose
 *  disorder is columnar -- random in space, perfectly correlated along
 *  imaginary time.  This is the McCoy-Wu random Ising model, with classical
 *  action
 *
 *      S = - sum_{tau,i} J_i S_i(tau) S_{i+1}(tau)
 *          - sum_{tau,i} J   S_i(tau) S_i(tau+1) ,
 *
 *  where the spatial couplings J_i are quenched, drawn once per column from a
 *  rectangular distribution of mean J and width DeltaJ, and the temporal
 *  couplings equal the tuning parameter J.  Increasing J drives the chain from
 *  the quantum-disordered phase into the ferromagnet through an
 *  infinite-randomness quantum critical point.
 *
 *  Method
 *  ------
 *  Single-cluster Wolff updates: a cluster is grown by adding aligned
 *  neighbours across a bond of coupling K with probability 1 - exp(-2K), then
 *  flipped as a whole.  This all but eliminates critical slowing down.  For each
 *  quenched disorder realization we accumulate the Monte Carlo averages of the
 *  squared and quartic magnetization, <m^2> and <m^4>; averaging these over
 *  realizations gives the magnetic Binder cumulant
 *
 *      V_m = 1 - [<m^4>] / (3 [<m^2>]^2)
 *
 *  ([...] = disorder average).  The size-independent crossing of V_m locates the
 *  critical coupling J_c.
 *
 *  Build:  g++ -O2 rtfim_wolff_qmc.cc -o rtfim_wolff_qmc
 *  Run:    ./rtfim_wolff_qmc L Ltau J DeltaJ N_real N_eq N_meas [seed]
 *  Output: one line per disorder realization:  "J  DeltaJ  L  Ltau  <m2>  <m4>"
 *          appended to  vm_L<L>_Lt<Ltau>.dat
 * ============================================================================
 */

#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <random>

int L, Lt, N;                       // spatial length, imaginary-time length, N=L*Lt
std::vector<signed char> spin;      // spins, index = i*Lt + tau
std::vector<double> Jx;             // spatial bond couplings per column i (random)
double Jt;                          // temporal bond coupling (= tuning parameter J)

std::mt19937_64 rng;
std::uniform_real_distribution<double> uni(0.0, 1.0);

inline int idx(int i, int t) { return i * Lt + t; }

// Draw a fresh columnar-disordered coupling set: J_i uniform in [J-DeltaJ/2, J+DeltaJ/2].
void init_disorder(double J, double DeltaJ)
{
    Jx.assign(L, 0.0);
    for (int i = 0; i < L; i++)
        Jx[i] = J - 0.5 * DeltaJ + DeltaJ * uni(rng);
    Jt = J;                          // temporal couplings are uniform
    for (int s = 0; s < N; s++)
        spin[s] = (uni(rng) < 0.5) ? 1 : -1;
}

// One single-cluster Wolff update.
void wolff_step()
{
    int i0 = (int)(uni(rng) * L);
    int t0 = (int)(uni(rng) * Lt);
    int seed = idx(i0, t0);
    signed char s0 = spin[seed];

    std::vector<int> stack;
    stack.push_back(seed);
    spin[seed] = -s0;                // flip on the fly

    while (!stack.empty())
    {
        int cur = stack.back(); stack.pop_back();
        int i = cur / Lt, t = cur % Lt;

        // four neighbours with their bond couplings
        int ip = (i + 1) % L, im = (i - 1 + L) % L;
        int tp = (t + 1) % Lt, tm = (t - 1 + Lt) % Lt;
        int nbr[4]      = { idx(ip, t), idx(im, t), idx(i, tp), idx(i, tm) };
        double coup[4]  = { Jx[i],       Jx[im],     Jt,         Jt        };

        for (int k = 0; k < 4; k++)
        {
            int nb = nbr[k];
            if (spin[nb] == s0)                                   // still aligned with old seed spin
                if (uni(rng) < 1.0 - std::exp(-2.0 * coup[k]))    // Wolff add probability
                {
                    spin[nb] = -s0;
                    stack.push_back(nb);
                }
        }
    }
}

double magnetization()
{
    long sum = 0;
    for (int s = 0; s < N; s++) sum += spin[s];
    return (double)sum / N;
}

int main(int argc, char **argv)
{
    if (argc < 8) {
        fprintf(stderr, "usage: %s L Ltau J DeltaJ N_real N_eq N_meas [seed]\n", argv[0]);
        return 1;
    }
    L          = atoi(argv[1]);
    Lt         = atoi(argv[2]);
    double J   = atof(argv[3]);
    double DJ  = atof(argv[4]);
    int N_real = atoi(argv[5]);      // disorder realizations
    int N_eq   = atoi(argv[6]);      // Wolff steps for equilibration
    int N_meas = atoi(argv[7]);      // measurement steps per realization
    unsigned long seed = (argc > 8) ? strtoul(argv[8], nullptr, 10) : 20160101UL;

    N = L * Lt;
    spin.resize(N);
    rng.seed(seed);

    char fname[128];
    snprintf(fname, sizeof fname, "vm_L%03d_Lt%04d.dat", L, Lt);
    FILE *fp = fopen(fname, "a");

    for (int r = 0; r < N_real; r++)
    {
        init_disorder(J, DJ);
        for (int e = 0; e < N_eq; e++) wolff_step();

        double m2 = 0.0, m4 = 0.0;
        for (int s = 0; s < N_meas; s++)
        {
            wolff_step();
            double m = magnetization();
            double mm = m * m;
            m2 += mm;
            m4 += mm * mm;
        }
        m2 /= N_meas;
        m4 /= N_meas;
        fprintf(fp, "%g\t%g\t%d\t%d\t%.8e\t%.8e\n", J, DJ, L, Lt, m2, m4);
    }
    fclose(fp);
    printf("done: L=%d Ltau=%d J=%g DeltaJ=%g realizations=%d -> %s\n",
           L, Lt, J, DJ, N_real, fname);
    return 0;
}
