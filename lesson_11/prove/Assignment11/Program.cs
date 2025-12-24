using System.Diagnostics;

namespace assignment11;

public class Assignment11
{   
    private const int NUM_WORKERS = 10;
    private const long START_NUMBER = 10_000_000_000;
    private const int RANGE_COUNT = 1_000_000;
    private static bool IsPrime(long n)
    {
        if (n <= 3) return n > 1;
        if (n % 2 == 0 || n % 3 == 0) return false;

        for (long i = 5; i * i <= n; i = i + 6)
        {
            if (n % i == 0 || n % (i + 2) == 0)
                return false;
        }
        return true;
    }

    public static void Main(string[] args)
    {
        // Use local variables for counting since we are in a single thread.
        int numbersProcessed = 0;
        int primeCount = 0;

        Queue<long> numberQueue = new Queue<long>();
        bool producerFinished = false;
        object mainLock = new object();
        object countLock = new object();
        object consoleLock = new object();

        Console.WriteLine("Prime numbers found:");

        var stopwatch = Stopwatch.StartNew();
        
        void WorkerCheckPrimes()
        {
            while (true)
            {
                long number;
                lock (mainLock)
                {
                    while (numberQueue.Count == 0 && !producerFinished)
                    {
                        Monitor.Wait(mainLock);
                    }

                    if (numberQueue.Count == 0 && producerFinished)
                    {
                        return;
                    }

                    number = numberQueue.Dequeue();
                }

                if (IsPrime(number))
                {
                    lock (countLock)
                    {
                        primeCount++;
                    }

                    lock (consoleLock)
                    {
                        Console.Write($"{number}, ");
                    }
                }
                
                lock (countLock)
                {
                    numbersProcessed++;
                }
            }
        }

        Thread[] threads = new Thread[NUM_WORKERS];
        for (int i = 0; i < NUM_WORKERS; i++)
        {
            
            threads[i] = new Thread(WorkerCheckPrimes);
            threads[i].Start();
        }

        for (long i = START_NUMBER; i < START_NUMBER + RANGE_COUNT; i++)
        {
            lock (mainLock)
            {
                numberQueue.Enqueue(i);
                Monitor.Pulse(mainLock);
            }
        }

        lock (mainLock)
        {
            producerFinished = true;
            Monitor.PulseAll(mainLock);
        }
        
        foreach (var t in threads)
        {
            t.Join();
        }

        stopwatch.Stop();

        Console.WriteLine(); // New line after all primes are printed
        Console.WriteLine();

        // Should find 43427 primes for range_count = 1000000
        Console.WriteLine($"Numbers processed = {numbersProcessed}");
        Console.WriteLine($"Primes found      = {primeCount}");
        Console.WriteLine($"Total time        = {stopwatch.Elapsed}");        
    }
}