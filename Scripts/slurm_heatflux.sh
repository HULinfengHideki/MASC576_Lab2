#!/bin/bash
#SBATCH -J hfL2T3
#SBATCH -p warshel
#SBATCH -N 3
#SBATCH -n 192
#SBATCH -t 10:00:00
#SBATCH -A warshel_155
#SBATCH -o slurm-heatflux-%j.out
#SBATCH -e slurm-heatflux-%j.err
#SBATCH --mem=0

module purge
module load usc intel-oneapi intel-oneapi-mpi cmake

lmp=/project2/knomura_125/26S/MASC576/harry/lammps/bin/lmp

echo "Job started on $(date)"
echo "Running in: $(pwd)"
echo "Input: in.heatflux"
echo "SLURM_JOB_NODELIST=${SLURM_JOB_NODELIST}"
echo "SLURM_NTASKS=${SLURM_NTASKS}"

mpiexec -n ${SLURM_NTASKS} ${lmp} -in in.heatflux > log.heatflux.txt 2>&1

cp -f Temperature.txt Temperature.heatflux.txt
cp -f dump.nve dump.heatflux.nve
cp -f SiC.restart SiC.heatflux.restart

echo "Job finished on $(date)"
