#!/bin/bash

echo "Watcher started at $(date)"
echo "Working directory: $(pwd)"

start_time=$(date +%s)
max_wait=$((72 * 3600))

while true; do
    now=$(date +%s)
    elapsed=$((now - start_time))

    if [ $elapsed -ge $max_wait ]; then
        echo "$(date) : Maximum wait time reached. Exiting watcher."
        break
    fi

    if [ -f "SiC.heatflux.restart" ] && [ ! -f ".submitted_1ns" ]; then
        echo "$(date) : Found SiC.heatflux.restart"
        sleep 30
        sbatch slurm_1ns_warshel64.sh
        touch .submitted_1ns
        echo "$(date) : Submitted slurm_1ns_warshel64.sh"
    fi

    if [ -f "SiC.relax1_1ns.restart" ] && [ ! -f ".submitted_2ns" ]; then
        echo "$(date) : Found SiC.relax1_1ns.restart"
        sleep 30
        sbatch slurm_2ns_warshel64.sh
        touch .submitted_2ns
        echo "$(date) : Submitted slurm_2ns_warshel64.sh"
    fi

    if [ -f "SiC.relax2_2ns.restart" ] && [ ! -f ".submitted_3ns" ]; then
        echo "$(date) : Found SiC.relax2_2ns.restart"
        sleep 30
        sbatch slurm_3ns_warshel64.sh
        touch .submitted_3ns
        echo "$(date) : Submitted slurm_3ns_warshel64.sh"
    fi

    if [ -f "SiC.relax3_3ns.restart" ] && [ ! -f ".submitted_4ns" ]; then
        echo "$(date) : Found SiC.relax3_3ns.restart"
        sleep 30
        sbatch slurm_4ns_warshel64.sh
        touch .submitted_4ns
        echo "$(date) : Submitted slurm_4ns_warshel64.sh"
    fi

    if [ -f ".submitted_1ns" ] && [ -f ".submitted_2ns" ] && [ -f ".submitted_3ns" ] && [ -f ".submitted_4ns" ]; then
        echo "$(date) : All follow-up jobs have been submitted. Exiting watcher."
        break
    fi

    sleep 60
done
