import time
import sympy
import concurrent.futures

def solve_with_timeout(expr, target, timeout=0.5):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(sympy.solve, expr, target)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            print(f"Timeout solving for {target}")
            return None
        except Exception as e:
            print(f"Error solving for {target}: {e}")
            return None

x, A, omega, t, phi = sympy.symbols('x A omega t phi')
expr = x - A * sympy.cos(omega * t + phi)

print("Solving for x...")
print("x =", solve_with_timeout(expr, x))

print("Solving for A...")
print("A =", solve_with_timeout(expr, A))

print("Solving for t (with 0.5s timeout)...")
start = time.time()
print("t =", solve_with_timeout(expr, t, timeout=0.5))
print(f"Solving for t finished in {time.time() - start:.4f} seconds")
