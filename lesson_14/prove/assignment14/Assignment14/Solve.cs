using System.Collections.Concurrent;
using Newtonsoft.Json.Linq;

namespace Assignment14;

public static class Solve
{
    private static readonly HttpClient HttpClient = new()
    {
        Timeout = TimeSpan.FromSeconds(180)
    };
    public const string TopApiUrl = "http://127.0.0.1:8123";

    // This function retrieves JSON from the server
    public static async Task<JObject?> GetDataFromServerAsync(string url)
    {
        try
        {
            var jsonString = await HttpClient.GetStringAsync(url);
            return JObject.Parse(jsonString);
        }
        catch (HttpRequestException e)
        {
            Console.WriteLine($"Error fetching data from {url}: {e.Message}");
            return null;
        }
    }

    // This function takes in a person ID and retrieves a Person object
    // Hint: It can be used in a "new List<Task<Person?>>()" list
    private static async Task<Person?> FetchPersonAsync(long personId)
    {
        var personJson = await Solve.GetDataFromServerAsync($"{Solve.TopApiUrl}/person/{personId}");
        return personJson != null ? Person.FromJson(personJson.ToString()) : null;
    }

    // This function takes in a family ID and retrieves a Family object
    // Hint: It can be used in a "new List<Task<Family?>>()" list
    private static async Task<Family?> FetchFamilyAsync(long familyId)
    {
        var familyJson = await Solve.GetDataFromServerAsync($"{Solve.TopApiUrl}/family/{familyId}");
        return familyJson != null ? Family.FromJson(familyJson.ToString()) : null;
    }
    
    // =======================================================================================================
    public static async Task<bool> DepthFS(long familyId, Tree tree)
    {
        if (familyId == 0) return false;
        var family = await FetchFamilyAsync(familyId);
        if (family == null) return false;

        lock (tree)
        {
            tree.AddFamily(family);
        }

        List<Task> tasks = new List<Task>();
        if (family.HusbandId != 0)
        {
            tasks.Add(Task.Run(async () =>
            {
                var husband = await FetchPersonAsync(family.HusbandId);
                if (husband != null)
                {
                    lock (tree) { tree.AddPerson(husband); }
                    if (husband.ParentId != 0)
                    {
                        await DepthFS(husband.ParentId, tree);
                    }
                }
            }));
        }

        if (family.WifeId != 0)
        {
            tasks.Add(Task.Run(async () =>
            {
                var wife = await FetchPersonAsync(family.WifeId);
                if (wife != null)
                {
                    lock (tree) { tree.AddPerson(wife); }
                    if (wife.ParentId != 0)
                    {
                        await DepthFS(wife.ParentId, tree);
                    }
                }
            }));
        }

        foreach (var childId in family.Children)
        {
            tasks.Add(Task.Run(async () =>
            {
                var child = await FetchPersonAsync(childId);
                if (child != null)
                {
                    lock (tree) { tree.AddPerson(child); }
                }
            }));
        }

        await Task.WhenAll(tasks);
        return true;
    }

    // =======================================================================================================
    public static async Task<bool> BreathFS(long startFamilyId, Tree tree)
    {
        if (startFamilyId == 0) return false;
        List<long> currentGenerationFamilies = new List<long> { startFamilyId };
        while (currentGenerationFamilies.Any())
        {
            var nextGenerationFamilies = new ConcurrentBag<long>();
            var tasks = new List<Task>();

            foreach (var famId in currentGenerationFamilies)
            {
                tasks.Add(Task.Run(async () =>
                {
                    var family = await FetchFamilyAsync(famId);
                    if (family == null) return;

                    lock (tree)
                    {
                        tree.AddFamily(family);
                    }

                    var peopleTasks = new List<Task>();
                    if (family.HusbandId != 0)
                    {
                        peopleTasks.Add(Task.Run(async () =>
                        {
                            var husband = await FetchPersonAsync(family.HusbandId);
                            if (husband != null)
                            {
                                lock (tree) { tree.AddPerson(husband); }
                                if (husband.ParentId != 0)
                                {
                                    nextGenerationFamilies.Add(husband.ParentId);
                                }
                            }
                        }));
                    }

                    if (family.WifeId != 0)
                    {
                        peopleTasks.Add(Task.Run(async () =>
                        {
                            var wife = await FetchPersonAsync(family.WifeId);
                            if (wife != null)
                            {
                                lock (tree) { tree.AddPerson(wife); }
                                if (wife.ParentId != 0)
                                {
                                    nextGenerationFamilies.Add(wife.ParentId);
                                }
                            }
                        }));
                    }

                    foreach (var childId in family.Children)
                    {
                        peopleTasks.Add(Task.Run(async () =>
                        {
                            var child = await FetchPersonAsync(childId);
                            if (child != null)
                            {
                                lock (tree) { tree.AddPerson(child); }
                            }
                        }));
                    }

                    await Task.WhenAll(peopleTasks);
                }));
            }

            await Task.WhenAll(tasks);
            currentGenerationFamilies = nextGenerationFamilies.Distinct().ToList();
        }
        return true;
    }
}
