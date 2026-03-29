#!/bin/bash
#SBATCH -J r2L2T3
#SBATCH -p warshel
#SBATCH -N 3
#SBATCH -n 192
#SBATCH -t 10:00:00
#SBATCH -A warshel_155
#SBATCH -o slurm-relax1-%j.out
#SBATCH -e slurm-relax1-%j.err
#SBATCH --mem=0

module purge
module load usc intel-oneapi intel-oneapi-mpi cmake

lmp=/project2/knomura_125/26S/MASC576/harry/lammps/bin/lmp

echo "Job started on $(date)"
echo "Running in: $(pwd)"
echo "Input: in.relax"
echo "SLURM_JOB_NODELIST=${SLURM_JOB_NODELIST}"
echo "SLURM_NTASKS=${SLURM_NTASKS}"

mpiexec -n ${SLURM_NTASKS} ${lmp} -in in.1ns.relax > log.relax2_2ns.txt 2>&1

cp -f Temperature.txt Temperature.relax2_2ns.txt

cp -f Temperature.relax2_2ns.txt Temperature.relax2_2ns_L200T300.txt
cp -f dump.nve dump.relax2_2ns.nve
cp -f SiC.restart SiC.relax2_2ns.restart

echo "Job finished on $(date)"
