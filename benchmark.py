import time
from app.src.modules.simulation_synthesis.service import generate_simulation_synthesis

prompt = "Explain me collision using cars as an example add sliders for mass and friction"

print("=" * 60)
print("EduSim Performance Benchmark")
print("=" * 60)

# Run 1 - Cold start (includes FAISS loading)
t0 = time.perf_counter()
result = generate_simulation_synthesis(prompt)
t1 = time.perf_counter()
print(f"\n🔵 Run 1 (Cold Start - includes FAISS load): {t1 - t0:.2f}s")

# Run 2 - Warm (FAISS already in memory)
t2 = time.perf_counter()
result2 = generate_simulation_synthesis(prompt)
t3 = time.perf_counter()
print(f"🟢 Run 2 (Warm - FAISS cached):              {t3 - t2:.2f}s")

# Run 3 - Warm again
t4 = time.perf_counter()
result3 = generate_simulation_synthesis("Show me projectile motion with adjustable angle and velocity")
t5 = time.perf_counter()
print(f"🟢 Run 3 (Warm - different query):            {t5 - t4:.2f}s")

print("\n" + "=" * 60)
print("DONE")
