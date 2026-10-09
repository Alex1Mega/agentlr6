import random
from collections import Counter

DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
SHIFTS = ["Ранкова", "Денна", "Нічна"]

REQUIREMENTS = {
    "Менеджер": 1,
    "Технік": 2,
    "Асистент": 3
}

SHIFT_STARTS = [6, 14, 22]
SHIFT_DURATION = 6
MIN_REST = 8
POPULATION_SIZE = 100
GENERATIONS = 300
MUTATION_RATE = 0.08
ELITE_COUNT = 5
random.seed(42)

workers = [
    {"name": "Працівник 1", "skill": "Технік",
     "unavailable": [(0, 0)], "preferred": [(1, 0)]},
    {"name": "Працівник 2", "skill": "Технік",
     "unavailable": [], "preferred": [(2, 1)]},
    {"name": "Працівник 3", "skill": "Технік",
     "unavailable": [(5, 2)], "preferred": [(4, 0)]},

    {"name": "Працівник 4", "skill": "Менеджер",
     "unavailable": [], "preferred": [(0, 0), (1, 0)]},
    {"name": "Працівник 5", "skill": "Менеджер",
     "unavailable": [(6, 2)], "preferred": [(5, 0)]},

    {"name": "Працівник 6", "skill": "Асистент",
     "unavailable": [], "preferred": [(0, 0)]},
    {"name": "Працівник 7", "skill": "Асистент",
     "unavailable": [(2, 1)], "preferred": [(3, 0)]},
    {"name": "Працівник 8", "skill": "Асистент",
     "unavailable": [], "preferred": [(4, 1)]},
    {"name": "Працівник 9", "skill": "Асистент",
     "unavailable": [(5, 0)], "preferred": [(6, 0)]},
    {"name": "Працівник 10", "skill": "Асистент",
     "unavailable": [], "preferred": [(1, 1)]}
]

# Кожен ген відповідає одному робочому місцю в зміні.
# Слоти зберігаються у форматі (день, зміна, спеціальність).
slots = []

for day in range(7):
    for shift in range(3):
        for skill, count in REQUIREMENTS.items():
            for _ in range(count):
                slots.append((day, shift, skill))

# Доступні кандидати для кожного слота.
# Недоступного працівника не можна призначити на зміну.
candidates = []

for day, shift, skill in slots:
    available = [
        i for i, worker in enumerate(workers)
        if worker["skill"] == skill
        and (day, shift) not in worker["unavailable"]
    ]

    if not available:
        raise ValueError(f"Немає доступних працівників: {day}, {shift}, {skill}")
    candidates.append(available)

# ОЦІНКА РОЗКЛАДУ
def fitness(schedule):
    cost = 0
    workload = Counter(schedule)

    # Штраф за надмірну кількість змін на тиждень.
    # Бажано працювати не більше 10 змін на тиждень.
    for i, worker in enumerate(workers):
        shifts_worked = workload[i]
        if shifts_worked > 10:
            cost += (shifts_worked - 10) * 20

    # Штраф за порушення мінімального відпочинку.
    assigned = [[] for _ in workers]

    for gene, (day, shift, skill) in zip(schedule, slots):
        start = day * 24 + SHIFT_STARTS[shift]
        end = start + SHIFT_DURATION
        assigned[gene].append((start, end))

    for i in range(len(workers)):
        times = sorted(assigned[i])

        for j in range(1, len(times)):
            previous_end = times[j - 1][1]
            current_start = times[j][0]

            rest = current_start - previous_end

            # Враховуємо перехід між неділею та понеділком.
            if rest < 0:
                rest += 7 * 24

            if rest < MIN_REST:
                cost += (MIN_REST - rest) * 10

    # Штраф за нерівномірне навантаження.
    loads = [workload[i] for i in range(len(workers))]
    average = sum(loads) / len(workers)

    for load in loads:
        cost += abs(load - average) * 2

    # Штраф за роботу у зміну, яка не є бажаною.
    for gene, (day, shift, skill) in zip(schedule, slots):
        preferred = workers[gene]["preferred"]

        if preferred and (day, shift) not in preferred:
            cost += 3

    # Штраф за три зміни поспіль у межах доби.
    for i in range(len(workers)):
        for day in range(7):
            worked_shifts = {
                shift
                for gene, (d, shift, skill) in zip(schedule, slots)
                if gene == i and d == day
            }

            if len(worked_shifts) == 3:
                cost += 30
    return cost


# ГЕНЕТИЧНИЙ АЛГОРИТМ
def create_individual():
    return [
        random.choice(allowed)
        for allowed in candidates
    ]


def crossover(parent1, parent2):
    child = []

    for i in range(len(slots)):
        gene = random.choice([parent1[i], parent2[i]])

        # Захист від призначення недоступного працівника.
        if gene not in candidates[i]: gene = random.choice(candidates[i])
        child.append(gene)

    return child


def mutate(individual):
    child = individual.copy()

    for i in range(len(child)):
        if random.random() < MUTATION_RATE:
            child[i] = random.choice(candidates[i])

    return child


def genetic_algorithm():
    population = [
        create_individual()
        for _ in range(POPULATION_SIZE)
    ]
    best = None

    for generation in range(GENERATIONS):
        population.sort(key=fitness)

        if best is None or fitness(population[0]) < fitness(best):
            best = population[0].copy()

        if fitness(best) == 0:
            break

        # Зберігаємо найкращі розв'язки.
        new_population = [
            individual.copy()
            for individual in population[:ELITE_COUNT]
        ]

        while len(new_population) < POPULATION_SIZE:
            parent1, parent2 = random.sample(population[:POPULATION_SIZE // 2], 2)
            child = crossover(parent1, parent2)
            child = mutate(child)
            new_population.append(child)

        population = new_population

    return best

def print_schedule(schedule):
    print("\nТИЖНЕВИЙ ГРАФІК РОБОТИ")
    for day in range(7):
        print(f"\n{DAYS[day]}")

        for shift in range(3):
            print(f"  {SHIFTS[shift]}:")

            for skill, required in REQUIREMENTS.items():
                assigned = [
                    workers[gene]["name"]
                    for gene, (d, s, sk) in zip(schedule, slots)
                    if d == day and s == shift and sk == skill
                ]

                print(f"    {skill} ({required}): "
                      f"{', '.join(assigned)}")

    print("\nНавантаження працівників:")

    counts = Counter(schedule)
    for i, worker in enumerate(workers):
        print(f"  {worker['name']} ({worker['skill']}): "
              f"{counts[i]} змін")

    print(f"\nЗагальна вартість розкладу: {fitness(schedule)}")

if __name__ == "__main__":
    best_schedule = genetic_algorithm()
    print_schedule(best_schedule)
