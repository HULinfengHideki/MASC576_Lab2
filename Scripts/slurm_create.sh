#!/bin/bash
#SBATCH -J crL2T3
#SBATCH -p warshel
#SBATCH -N 3
#SBATCH -n 192
#SBATCH -t 10:00:00
#SBATCH -A warshel_155
#SBATCH -o slurm-create-%j.out
#SBATCH -e slurm-create-%j.err
#SBATCH --mem=0

module purge
module load usc intel-oneapi intel-oneapi-mpi cmake

lmp=/project2/knomura_125/26S/MASC576/harry/lammps/bin/lmp

echo "Job started on $(date)"
echo "Running in: $(pwd)"
echo "Using input: in.create"
echo "SLURM_NTASKS=${SLURM_NTASKS}"
echo "SLURM_JOB_NODELIST=${SLURM_JOB_NODELIST}"

scontrol show hostnames "$SLURM_JOB_NODELIST"

mpiexec -n 192 ${lmp} -in in.create > log.create.txt 2>&1
cp -f SiC.restart SiC.create.restart
echo "Job finished on $(date)"
