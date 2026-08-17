#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <fstream>

using namespace std;

//-----------------------------------------------------------
//	constants definition
//-----------------------------------------------------------
const double PI 	= 4*atan(1.0);	// the constant PI
const int N_T 		= 1;			// number of spin colors
const int Lx 		= lxv;			// length size of the lattice
const int Ly 		= ltv;			// length size of the lattice
const int N 		= Lx*Ly;		// # of spins in each color, used for screw boundary conditions.
const int N_EQ 		= 1000000;		// default 1,000,000
const int N_C 		= 10;			//total MT configurations.
const int N_S 		= 10000;		// steps in each configuration; default 10000
const int N_cor 	= 201;			// time length to be considered

const double J		= 0.442;
const double DeltaJ = 0.20;
const double K 		= 0;
const double DeltaK = 0;
// the coupling constant

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

public:
	void initialspin();
	void initialspinup();
	// void output(char *plotname);
	void setup(double Jc, double DeltaJ, double Kc, double DeltaK);
	void step();

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
			}
		}
		//consider the spin to the down of current one.
	}
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

	char format[] = "eqMK%iDK%iDJ%iL%ix%iJ%g.txt";
	char datFile[sizeof format+24];
	sprintf(datFile, format, (int)(K*100), (int)(DeltaK*100), (int)(DeltaJ*100), Lx, Ly, J*1000000);

	FILE *df;

	clock_t start = clock();

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
		fprintf(df, "%i\t %f\t %f\n", bn, stat[bn].readmean(), ((double)clock() - start) / CLOCKS_PER_SEC / 60);
		fclose(df);
		// stat[(bn+1)%bins].add(stat[bn].readmean());
	}
}

void mFct()
{
	spinClass spin;
	statClass stat;

	char format[] = "mK%02iDK%02iDJ%02iL%02ix%02i.txt";
	char datFile[sizeof format+24];
	sprintf(datFile, format, (int)(K*100), (int)(DeltaK*100), (int)(DeltaJ*100), Lx, Ly);

	FILE *df;

	stat.initialstat();

	for (int nc = 0; nc < N_C; nc++)
	{
		spin.setup(J,DeltaJ,K,DeltaK);
		spin.initialspin();

		for (int neq = 0; neq < N_EQ; neq++) spin.step();

		for(int ns = 0; ns < N_S; ns++)
		{
			for(int k = 0; k < 20; k++) spin.step();
			stat.add(spin.magnetization_abs());
		}
	}
	df = fopen(datFile,"a");
	fprintf(df,"%f\t %f\t %f\n", J, stat.readmean(), stat.readstd());
	fclose(df);
}

void vmFct()
{
	spinClass spin;
	statClass stat[2];

	char format[] = "vmK%02iDK%02iDJ%02iL%02ix%02i.txt";
	char datFile[sizeof format+24];
	sprintf(datFile, format, (int)(K*100), (int)(DeltaK*100), (int)(DeltaJ*100), Lx, Ly);

	FILE *df;

	stat[0].initialstat();
	stat[1].initialstat();

	for(int nc = 0; nc < N_C; nc++)
	{
		spin.setup(J,DeltaJ,K,DeltaK);
		spin.initialspin();

		for(int neq = 0; neq < N_EQ; neq++) spin.step();

		for(int ns = 0; ns < N_S; ns++)
		{
			stat[0].add(spin.magnetization_abs()*spin.magnetization_abs()*spin.magnetization_abs()*spin.magnetization_abs());
			stat[1].add(spin.magnetization_abs()*spin.magnetization_abs());
			for(int k = 0; k < 20; k++) spin.step();
		}
	}
	df = fopen(datFile,"a");
	fprintf(df,"%f\t %f\n", J, 1-stat[0].readmean()/(3*stat[1].readmean()*stat[1].readmean()));
	fclose(df);
}

void vmFctHlf()
{
	spinClass spin;
	statClass stat[2];

	char format[] = "vmK%02iDK%02iDJ%02iL%02ix%02iJ%g";
	char datFile[sizeof format+24];
	sprintf(datFile, format, (int)(K*100), (int)(DeltaK*100), (int)(DeltaJ*100), Lx, Ly, J*1000);

	FILE *df;

	for(int nc = 0; nc < N_C; nc++)
	{
		spin.setup(J,DeltaJ,K,DeltaK);
		spin.initialspin();
		stat[0].initialstat();
		stat[1].initialstat();

		for(int neq = 0; neq < N_EQ; neq++) spin.step();

		for(int ns = 0; ns < N_S; ns++)
		{
			stat[0].add(spin.magnetization_abs()*spin.magnetization_abs()*spin.magnetization_abs()*spin.magnetization_abs());
			stat[1].add(spin.magnetization_abs()*spin.magnetization_abs());
			for(int k = 0; k < 20; k++) spin.step();
		}
		df = fopen(datFile,"a");
		fprintf(df,"%f\t %f\t", stat[0].readmean(), stat[1].readmean());
		fclose(df);
	}
}

void vmFctHlf2()
{
	spinClass spin;

	char format[] = "vmK%02iDK%02iDJ%02iL%02ix%02iJ%g";
	char datFile[sizeof format+24];
	sprintf(datFile, format, (int)(K*100), (int)(DeltaK*100), (int)(DeltaJ*100), Lx, Ly, J*1000);

	FILE *df;

	for(int nc = 0; nc < N_C; nc++)
	{
		double temp[N_S] = {};
		spin.setup(J,DeltaJ,K,DeltaK);
		spin.initialspin();

		for(int neq = 0; neq < N_EQ; neq++) spin.step();

		for(int ns = 0; ns < N_S; ns++)
		{
			temp[ns] = spin.magnetization_abs();
			for(int k = 0; k < 20; k++) spin.step();
		}
		
		df = fopen(datFile,"a");
		for(int ns = 0; ns < N_S; ns++)	fprintf(df,"%f\t", temp[ns]);
		fprintf(df,"\n");
		fclose(df);
	}
}

void xcorFctHlf()
{
	spinClass spin;
	statClass stat[Lx/2];

	char format[] = "xcorK%02iDK%02iDJ%02iL%02ix%02iJ%g";
	char datFile[sizeof format+24];
	sprintf(datFile,format,(int)(K*100),(int)(DeltaK*100),(int)(DeltaJ*100),Lx,Ly,J*1000000);

	FILE *df;

	for(int nc = 0; nc < N_C; nc++)
	{
		spin.setup(J,DeltaJ,K,DeltaK);
		spin.initialspin();
		for (int x = 0; x < Lx/2; ++x)
			stat[x].initialstat();

		for(int neq = 0; neq < N_EQ; neq++) spin.step();

		for(int ns = 0; ns < N_S; ns++)
		{
			for (int x = 0; x < Lx/2; x++)
				stat[x].add(spin.corr_x(x+1));

			for(int k = 0; k < 20; k++) spin.step();
		}

		df = fopen(datFile,"a");
		for (int x = 0; x < Lx/2; ++x)
			fprintf(df,"%f\t", stat[x].readmean());
		fprintf(df, "\n");
		fclose(df);
	}
}

void xcorFctHlf_hlfL()
{
	spinClass spin;
	statClass stat;

	char format[] = "xcorK%02iDK%02iDJ%02iL%02ix%02iJ%g_hlfL";
	char datFile[sizeof format+24];
	sprintf(datFile, format, (int)(K*100), (int)(DeltaK*100), (int)(DeltaJ*100), Lx, Ly, J*1000000);

	FILE *df;

	for(int nc = 0; nc < N_C; nc++)
	{
		spin.setup(J,DeltaJ,K,DeltaK);
		spin.initialspin();
		stat.initialstat();

		for(int neq = 0; neq < N_EQ; neq++) spin.step();

		for(int ns = 0; ns < N_S; ns++)
		{
			stat.add(spin.corr_x_hlfL());
			for(int k = 0; k < 20; k++) spin.step();
		}

		df = fopen(datFile,"a");
		fprintf(df,"%f\n", stat.readmean());
		fclose(df);
	}
}

void chiLocLinFctHlf()
{
	spinClass spin;
	statClass stat;

	char format[] = "chilocLinK%02iDK%02iDJ%02iL%02ix%02iJ%g";
	char datFile[sizeof format+20];
	sprintf(datFile, format, (int)(K*100), (int)(DeltaK*100), (int)(DeltaJ*100), Lx, Ly, J*1000000);

	FILE *df;

	for (int nc = 0; nc < N_C; ++nc)
	{
		spin.setup(J,DeltaJ,K,DeltaK);
		spin.initialspin();
		stat.initialstat();

		for (int neq = 0; neq < N_EQ; ++neq) spin.step();

		for (int ns = 0; ns < N_S; ++ns)
		{
			for (int i = 0; i < 20; ++i) spin.step();
			for (int nt = 0; nt < N_T; ++nt)
				for (int x = Lx/4; x < Lx/2; x += 2)
					// stat.add(pow(spin.chi_m2(nt, x),2));
					stat.add(spin.chi_ss(nt, x));
		}
		df = fopen(datFile, "a");
		fprintf(df, "%f\t", stat.readmean());
		fclose(df);
	}
}

void chiLocNonLinFctHlf()
{
	spinClass spin;
	statClass stat4;
	statClass stat2;

	double mlocal;

	char format[] = "chilocNonLinK%02iDK%02iDJ%02iL%02ix%02iJ%g";
	char datFile[sizeof format+20];
	sprintf(datFile, format, (int)(K*100), (int)(DeltaK*100), (int)(DeltaJ*100), Lx, Ly, J*1000000);

	FILE *df;

	for (int nc = 0; nc < N_C; ++nc)
	{
		spin.setup(J,DeltaJ,K,DeltaK);
		spin.initialspin();
		stat4.initialstat();
		stat2.initialstat();

		for (int neq = 0; neq < N_EQ; ++neq) spin.step();

		for (int ns = 0; ns < N_S; ++ns)
		{
			for (int i = 0; i < 20; ++i) spin.step();
			for (int nt = 0; nt < N_T; ++nt)
				for (int x = Lx/4; x < Lx/2; x += 2)
				{
					mlocal = spin.chi_m2(nt, x);
					stat4.add(pow(mlocal,4));
					stat2.add(pow(mlocal,2));
				}
		}
		df = fopen(datFile, "a");
		fprintf(df, "%f\t", -(stat4.readmean()-3*stat2.readmean()*stat2.readmean())/(6*Ly));
		fclose(df);
	}
}

/* ******************************************* */

int main ()
{
	srand48(time(NULL));

	vmFctHlf2();

	return 0;
}
