#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <fstream>
#include <set>

using namespace std;

//-----------------------------------------------------------
//	constants definition
//-----------------------------------------------------------
const double PI 	= 4*atan(1.0);	// the constant PI
const int N_T 		= 3;			// number of spin colors
const int Lx 		= 32;			// length size of the lattice
const int Ly 		= 32;			// length size of the lattice
const int N 		= Lx*Ly;		// # of spins in each color, used for screw boundary conditions.
const int N_EQ 		= 1000000;		// default 1,000,000
const int N_C 		= 10;			//total MT configurations.
const int N_S 		= 10000;		// steps in each configuration; default 10000
const int N_cor 	= 201;			// time length to be considered

const double J		= 0.240;
const double DeltaJ = 0.20;
const double K 		= 0.08;
const double DeltaK = 0.04;
// the coupling constant

int sweep = 0;

/* ******************************************* */

class statClass
{
private:
	double mean;
	double std;
	unsigned int count;

public:
	void initialstat(void);// initialize the counter
	void add(double value);// add a data to stat

	double pwr2(double value);
	double pwr4(double value);

	double readmean(void);
	double readstd(void);
	double readaccuracy(void);
};

void statClass::initialstat(void)
{
	mean  = 0.0;
	std   = 0.0;
	count = 0;
}

void statClass::add(double value)
{
	mean += value;
	std  += value*value;
	count++;
}

double statClass::readmean(void)
{
	return mean/count;
}

double statClass::readstd(void)
{
	return sqrt(std/count-(mean/count)*(mean/count));
}

double statClass::readaccuracy(void)
{
	if(count >=10 )
		return sqrt(std/count-(mean*mean)/(count*count))/mean;
	else
		return 10.0;
}

/* ******************************************* */

class spinClass
{
private:
	int spin[N_T][N];		// spin configuration

	double J_ccX[N];		// coupling constant J in x direction
	double J_ccY[N];		// coupling constant J in y direction

	double K_ccX[N];
	double K_ccY[N];

	double E0;				// maximum of local energy density, used in Monte Carlo

	double p_addX[2][N_T][N];	// critical probability to add a bound into cluster
	double p_addY[2][N_T][N];	// critical probability to add a bound into cluster

	set<int> latticeSitesSet;


public:
	void initialspin();
	void initialspinup();
	// void output(char *plotname);
	void setup(double Jc, double DeltaJ, double Kc, double DeltaK);
	void step();

	void setuplatticeSitesSet();
	void visitedSpins(int i);
	int print(int i);

	double energy();
	double energy1();
	double energy2();
	// double energy3(void);

	// double energy_sqr(double Jc);
	// double energy_ssqr(double Jc);

	double corr_t(int t);
	double corr_x(int x);
	double corr_x_hlfL();

	double chi_m2(int color, int x);
	double chi_ss(int color, int x);

	double magnetization();
	double magnetization_abs();
	double magnetization_sqr();
	double magnetization_ssqr();
	double magnetization(int color);
	double magnetization(int color1, int color2);

	double magnetization_abs_energy();
	double magnetization_sqr_energy();
	// double magnetization_cubed_energy();
	double magnetization_ssqr_energy();
};

void spinClass::initialspin() // initialize lattice sites with random up/down spins
{
	for (int t=0; t < N_T; t++)
	{
		for (int i=0; i < N; i++)
		{
			if(drand48() > 0.5) spin[t][i]=1;
			else spin[t][i]=-1;
		}
	}
}

double spinClass::energy1()
{
	double temp;
	temp=0.0;

	for (int t=0; t < N_T; t++)
	{
		for (int i=0; i < N; i++)
		{
			int nn;
			int xcor,ycor;

			xcor = i%Lx;
			ycor = i/Lx;

			if( (nn = xcor + 1) >= Lx ) nn -= Lx;
			nn = ycor*Lx + nn;
			temp += J_ccX[i]*spin[t][i]*spin[t][nn];

			if( (nn = ycor + 1) >= Ly ) nn -= Ly;
			nn = nn*Lx + xcor;
			temp += J_ccY[i]*spin[t][i]*spin[t][nn];
			// find nn by periodic BC, and compute energy: sum(J_ij-J)...
		}
	}
	return -temp/(N*N_T);
}

double spinClass::energy2()
{
	double temp;
	temp=0.0;

	for (int t=0; t < N_T; t++)
	{
		for (int s=t+1; s < N_T; s++)
		{
			for (int i=0; i < N; i++)
			{
				int nn;
				int xcor,ycor;

				xcor = i%Lx;
				ycor = i/Lx;

				if( (nn = xcor + 1) >= Lx ) nn -= Lx;
				nn = ycor*Lx + nn;
				temp += 2*K_ccX[i]*spin[t][i]*spin[t][nn]*spin[s][i]*spin[s][nn];

				if( (nn = ycor + 1) >= Ly ) nn -= Ly;
				nn = nn*Lx + xcor;
				temp += 2*K_ccY[i]*spin[t][i]*spin[t][nn]*spin[s][i]*spin[s][nn];
				// find nn by periodic BC, and compute energy: 4-spin term
			}
		}
	}
	return -temp/(N*N_T);
}

double spinClass::energy()
{
	return energy1() + energy2();
}

void spinClass::setup(double Jc, double DeltaJ, double Kc, double DeltaK)
{
	// The couplings in the y-direction are kept constant at Jc or Kc.
	// The couplings in the x-direction are random but the same within each column.
	for(int i = 0; i < Lx; i++)
	{
		K_ccX[i] = (drand48()*DeltaK) + (Kc - (DeltaK/2.0));
		K_ccY[i] = Kc;
	}
	for(int i = 0; i < N; i++)
	{
		K_ccX[i] = K_ccX[i%Lx];
		K_ccY[i] = Kc;
	}

	for(int i = 0; i < Lx; i++)
	{
		J_ccX[i] = (drand48()*DeltaJ) + (Jc - (DeltaJ/2.0));
		J_ccY[i] = Jc;
	}
	for(int i = 0; i < N; i++)
	{
		J_ccX[i] = J_ccX[i%Lx];
		J_ccY[i] = Jc;
	}

	E0 = Jc + DeltaJ/2.0 + 2 * (Kc + DeltaK/2.0) * (N_T-1);

	for(int site = 0; site < N; site++)
	{
		for(int Eoff = 0; Eoff < N_T; Eoff++)
		{
			p_addX[0][Eoff][site] = J_ccX[site] + 2.0 * K_ccX[site] * ( 2.0 * Eoff - (N_T-1) );
			p_addX[1][Eoff][site] = - p_addX[0][Eoff][site];
			p_addY[0][Eoff][site] = J_ccY[site] + 2.0 * K_ccY[site] * ( 2.0 * Eoff - (N_T-1) );
			p_addY[1][Eoff][site] = - p_addY[0][Eoff][site];
			//calculate energy

			p_addX[0][Eoff][site] = 1.0 - exp( p_addX[0][Eoff][site] - E0);
			p_addX[1][Eoff][site] = 1.0 - exp( p_addX[1][Eoff][site] - E0);
			p_addY[0][Eoff][site] = 1.0 - exp( p_addY[0][Eoff][site] - E0);
			p_addY[1][Eoff][site] = 1.0 - exp( p_addY[1][Eoff][site] - E0);
			//calculate probablity.
		}
	}
	//the index of p_addX[2][N_T][N]
	// fir: index is 0 means S_i*S_j of currenttype is -1, else is 1
	// sec: index x means sum_{not in current} S_i*S_j is 2x-(N_T-1).
	// thr: location of bounds.

	return;
}

void spinClass::step()
{
	//double temp;
	//probability to add a spin into cluster.

	int is, it;
	int sp;
	int current;
	int nn;
	int xcor, ycor;
	int stack[N];
	int flag[N];
	int Eon, Eoff;

	for(int i=0; i < N; i++)
		flag[i]=0;
	//initialize flag, 0--not in cluster, 1 in cluster

	is = (int) (N*drand48());
	it = (int) (N_T*drand48());
	// choose a spin in a color

	stack[0] = is;
	flag[is]=1;
	sp = 1;
	//oldspin = spin[it][is];
	//newspin = -spin[it][is];
	spin[it][is] = -spin[it][is];

	while (sp)
	{
		current = stack[--sp];

		xcor = current%Lx;
		ycor = current/Lx;

		if( (nn = xcor + 1) >= Lx) nn -= Lx;
		nn = ycor*Lx + nn;
		if(flag[nn]==0)
		{
			Eon = (-spin[it][current]*spin[it][nn]+1)/2;
			Eoff = 0;
			for (int t=0; t < N_T; t++)
			{
				if(t != it)
				{
					Eoff = Eoff + (spin[t][current]*spin[t][nn]+1)/2;
				}
			}
			if(drand48() < p_addX[Eon][Eoff][current])
			{
				stack[sp++] = nn;
				flag[nn] = 1;
				spin[it][nn] = -spin[it][nn];
				visitedSpins(it*N+nn);
			}
		}
		//consider the spin to the right of current one.


		if( (nn = xcor - 1) < 0) nn += Lx;
		nn = ycor*Lx + nn;
		if(flag[nn]==0)
		{
			Eon = (-spin[it][current]*spin[it][nn]+1)/2;
			Eoff = 0;
			for (int t=0; t < N_T; t++)
			{
				if(t != it)
				{
					Eoff = Eoff + (spin[t][current]*spin[t][nn]+1)/2;
				}
			}
			if(drand48() < p_addX[Eon][Eoff][nn])
			{
				stack[sp++] = nn;
				flag[nn] = 1;
				spin[it][nn] = -spin[it][nn];
				visitedSpins(it*N+nn);
			}
		}
		//consider the spin to the left of current one.


		if( (nn = ycor + 1) >= Ly) nn -= Ly;
		nn = nn*Lx + xcor;
		if(flag[nn]==0)
		{
			Eon = (-spin[it][current]*spin[it][nn]+1)/2;
			Eoff = 0;
			for (int t=0; t < N_T; t++)
			{
				if(t != it)
				{
					Eoff = Eoff + (spin[t][current]*spin[t][nn]+1)/2;
				}
			}
			if(drand48() < p_addY[Eon][Eoff][current])
			{
				stack[sp++] = nn;
				flag[nn] = 1;
				spin[it][nn] = -spin[it][nn];
				visitedSpins(it*N+nn);
			}
		}
		//consider the spin to the up of current one.


		if( (nn = ycor - 1) < 0) nn += Ly;
		nn = nn*Lx + xcor;
		if(flag[nn]==0)
		{
			Eon = (-spin[it][current]*spin[it][nn]+1)/2;
			Eoff = 0;
			for (int t=0; t < N_T; t++)
			{
				if(t != it)
				{
					Eoff = Eoff + (spin[t][current]*spin[t][nn]+1)/2;
				}
			}
			if(drand48() < p_addY[Eon][Eoff][nn])
			{
				stack[sp++] = nn;
				flag[nn] = 1;
				spin[it][nn] = -spin[it][nn];
				visitedSpins(it*N+nn);
			}
		}
		//consider the spin to the down of current one.
	}
}

void spinClass::setuplatticeSitesSet()
{
	for (int j = 0; j < N_T*N; ++j) latticeSitesSet.insert(j);

	// latticeSitesSet.erase(4);

	// std::set<int>::iterator it;
	// cout<<latticeSitesSet.size()<<endl;
	// int ii=0;
	// for (it=latticeSitesSet.begin(); it!=latticeSitesSet.end(); ++it)
	//     std::cout << ' ' << *it;
	// std::cout << '\n';

}

void spinClass::visitedSpins(int i)
{
	latticeSitesSet.erase(i);

	if (latticeSitesSet.size() == 0)
	{
		sweep++;
		// printf("%i\n", sweep);
		setuplatticeSitesSet();
	}
	// latticeSitesSet.insert(i);

	// set<int> sampleSet;
	// sampleSet.insert(1);
	// int sampleArray[N] = {1, 2, 3, 4, 5, 6, 7};
	// printf("%i\n", i);

	// for (int j=0; j<N; ++j) latticeSitesSet.insert(j);

	// printf("%i\n", i);

	// if (latticeSitesSet == sampleSet)
	// {
	// 	printf("%s\n", "sweep");
	// 	latticeSitesSet.clear();
	// }
	// return i;
}

int spinClass::print(int i)
{
	return i;
}

double spinClass::corr_t(int t)
{
	double temp = 0.0;
	for (int color = 0; color < N_T; color++)
		for (int i = 0; i < N; i++)
			temp += (double)spin[color][i]*(double)spin[color][(i+(t*Lx))%N];
	temp /= (N_T*N);
	return temp;
}

double spinClass::corr_x(int x)
{
	double temp = 0.0;
	for (int color = 0; color < N_T; color++)
		for (int i = 0; i < N; i++)
			temp += (double)spin[color][i]*(double)spin[color][(i+x) >= (i/Lx+1)*Lx ? (i+x-Lx):(i+x)];
	temp /= (N_T*N);
	return temp;
}

double spinClass::corr_x_hlfL()
{
	double temp = 0.0;
	for (int color = 0; color < N_T; color++)
		for (int y = 0; y < Ly; ++y)
			for (int x = 0; x < Lx/2; ++x)
				temp += (double)spin[color][(y*Lx)+x]*(double)spin[color][(y*Lx)+x+(Lx/2)];
	temp /= (N_T*N/2);
	return temp;
}

double spinClass::chi_m2(int color, int x)
{
	double temp = 0.0;
	for (int y = 0; y < Ly; ++y)
		temp += (double)spin[color][(x+(y*Lx))];
	return temp;
}

double spinClass::chi_ss(int color, int x)
{
	double temp = 0.0;
	for (int y = 1; y < Ly; ++y)
		temp += (double)spin[color][(x+(y*Lx))];
	return (double)spin[color][x]*temp;
}

double spinClass::magnetization(int color)
{
	double temp = 0.0;
	for (int i = 0; i < N; i++)
		temp += (double)spin[color][i];
	temp /= N;
	return temp;
}

double spinClass::magnetization()
{
	double temp = 0.0;
	for(int t=0; t < N_T; t++)
		temp += magnetization(t);
	temp /= N_T;
	return temp;
}

double spinClass::magnetization_abs()
{
	double temp = 0.0;
	for(int t=0; t < N_T; t++)
		temp += fabs(magnetization(t));
	temp /= N_T;
	return temp;
}

double spinClass::magnetization_sqr()
{
	double mgz = 0.0;
	double temp = 0.0;
	for(int t=0; t < N_T; t++)
	{
		mgz = magnetization(t);
		temp += mgz*mgz;
	}
	temp /= N_T;
	return temp;
}

double spinClass::magnetization_ssqr()
{
	double temp = 0.0;
	double mgz = 0.0;
	for(int t=0; t < N_T; t++)
	{
		mgz = magnetization(t);
		temp += mgz*mgz*mgz*mgz;
	}
	temp /= N_T;
	return temp;
}

double spinClass::magnetization(int color1, int color2)
{
	double temp = 0.0;
	for (int i = 0; i < N; i++)
		temp += (double)(spin[color1][i]*spin[color2][i]);
	temp /= N;
	return fabs(temp);
}

double spinClass::magnetization_abs_energy()
{
	double temp = 0.0;
	for(int t=0; t < N_T; t++)
		temp += (fabs(magnetization(t))*energy());
	temp /= N_T;
	return temp;
}

double spinClass::magnetization_sqr_energy()
{
	double mgz = 0.0;
	double temp = 0.0;
	for(int t=0; t < N_T; t++)
	{
		mgz = magnetization(t);
		temp += (mgz*mgz*energy());
	}
	temp /= N_T;
	return temp;
}

double spinClass::magnetization_ssqr_energy()
{
	double mgz = 0.0;
	double temp = 0.0;
	for(int t=0; t < N_T; t++)
	{
		mgz = magnetization(t);
		temp += (mgz*mgz*mgz*mgz*energy());
	}
	temp /= N_T;
	return temp;
}

/* ******************************************* */

void eqTMFct()
{
	const int bins = 23;

	spinClass spin;
	statClass stat[bins];

	char format[] = "eqMNt%iL%02ix%02iJ%gDJ%02iK%02iDK%02i";
	char datFile[sizeof format+24];
	sprintf(datFile, format, N_T, Lx, Ly, J*1000, (int)(DeltaJ*100), (int)(K*100), (int)(DeltaK*100));

	FILE *df;

	clock_t start = clock();

	spin.setuplatticeSitesSet();
	spin.setup(J,DeltaJ,K,DeltaK);
	spin.initialspin();
	for (int st = 0; st < bins; ++st)
		stat[st].initialstat();


	for(int bn = 0; bn < bins; bn++)
	{
		for(int k = 0; k < pow(2,bn); k++)
		{
			spin.step();
			stat[bn].add(spin.magnetization_abs());
		}
		df = fopen(datFile, "a");
		fprintf(df, "%i\t %f\t %i\t %f\n", bn, stat[bn].readmean(), spin.print(sweep), ((double)clock() - start) / CLOCKS_PER_SEC / 60);
		fclose(df);
		// stat[(bn+1)%bins].add(stat[bn].readmean());
	}
}

void sweepCount()
{
	spinClass spin;

	char format[] = "sweepCountNt%iL%02ix%02iJ%gDJ%02iK%02iDK%02i";
	char datFile[sizeof format+24];
	sprintf(datFile, format, N_T, Lx, Ly, J*1000, (int)(DeltaJ*100), (int)(K*100), (int)(DeltaK*100));

	FILE *df;

	for(int nc = 0; nc < N_C; nc++)
	{
		spin.setuplatticeSitesSet();
		spin.setup(J,DeltaJ,K,DeltaK);
		spin.initialspin();

		for(int neq = 0; neq < N_EQ; neq++) 
		{
			spin.step();
		}

		// cout << spin.print(sweep) << endl;
			
		df = fopen(datFile,"a");
		fprintf(df,"%i\t", spin.print(sweep));
		fclose(df);
	}
}

/* ******************************************* */

int main ()
{
	srand48(time(NULL));

	eqTMFct();

	return 0;
}
