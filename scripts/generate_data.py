import numpy as np
import pandas as pd
from pathlib import Path

# Creates fake telehealth data for the pipeline.
# The data is messy on purpose (duplicates, mixed date formats, different casing,
# missing and wrong values) so the silver layer has real cleaning to do.

np.random.seed(42)

RAW_DIR = Path(__file__).resolve().parents[1] / 'data' / 'raw'
RAW_DIR.mkdir(parents=True, exist_ok=True)

first_names = ['Omar', 'Lina', 'Sara', 'Adam', 'Noor', 'Yousef', 'Maya', 'Karim',
               'Hana', 'Sami', 'Rana', 'Ali', 'Dina', 'Tariq', 'Leila', 'Zaid']
last_names = ['Haddad', 'Nasser', 'Khalil', 'Saleh', 'Mansour', 'Awad', 'Qasem', 'Darwish']
states = ['CA', 'TX', 'NY', 'FL', 'WA', 'IL', 'CO', 'AZ']
genders = ['M', 'F', 'male', 'Female', 'MALE', 'f', '']
providers = ['Dr. Smith', 'Dr. Patel', 'Dr. Garcia', 'Dr. Lee', 'Dr. Brown']
statuses = ['completed', 'Completed', 'COMPLETED', 'cancelled', 'Canceled', 'no_show', 'No Show']

# appointment type -> price in USD
appt_prices = {'Initial Consultation': 149.0, 'Follow-up': 79.0, 'Lab Review': 59.0}

# test name -> (unit, normal low, normal high, min value, max value)
lab_tests = {
    'Testosterone':    ('ng/dL', 300, 1000, 150, 1200),
    'Vitamin D':       ('ng/mL', 30, 100, 10, 110),
    'HbA1c':           ('%', 4.0, 5.6, 4.0, 8.5),
    'LDL Cholesterol': ('mg/dL', 0, 100, 50, 200),
}

start = pd.Timestamp('2024-01-01')
end = pd.Timestamp('2025-12-31')


def random_dates(low, high, n):
    seconds = np.random.randint(0, int((high - low).total_seconds()), n)
    return low + pd.to_timedelta(seconds, unit='s')


def messy_date(d):
    # same date but written in different formats
    fmt = np.random.choice(['%Y-%m-%d', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'])
    return d.strftime(fmt)


def make_patients(n=500):
    ids = [f'P{i:05d}' for i in range(1, n + 1)]
    first = np.random.choice(first_names, n)
    last = np.random.choice(last_names, n)
    dob = random_dates(pd.Timestamp('1955-01-01'), pd.Timestamp('2002-12-31'), n)
    signup = random_dates(start, end - pd.Timedelta(days=60), n)

    emails = [f'{f}.{l}{i}@example.com' for f, l, i in zip(first, last, range(1, n + 1))]
    emails = [np.random.choice([e, e.upper(), e, '']) for e in emails]

    state = np.random.choice(states, n)
    state = [np.random.choice([s, s.lower(), f' {s} ']) for s in state]

    patients = pd.DataFrame({
        'patient_id': ids,
        'first_name': first,
        'last_name': last,
        'gender': np.random.choice(genders, n),
        'date_of_birth': [messy_date(d) for d in dob],
        'state': state,
        'email': emails,
        'signup_at': signup.strftime('%Y-%m-%d %H:%M:%S'),
    })

    # the same patients exported twice
    duplicates = patients.sample(25, random_state=42)
    return pd.concat([patients, duplicates], ignore_index=True)


def make_appointments(patients):
    rows = []
    for _, p in patients.drop_duplicates('patient_id').iterrows():
        signup = pd.Timestamp(p['signup_at'])
        n = np.random.randint(0, 9)
        for d in random_dates(signup, end, n):
            appt_type = np.random.choice(list(appt_prices))
            rows.append({
                'patient_id': p['patient_id'],
                'provider_name': np.random.choice(providers),
                'appointment_type': appt_type,
                'scheduled_at': d.strftime('%Y-%m-%d %H:%M:%S'),
                'status': np.random.choice(statuses),
                'duration_minutes': np.random.choice(['15', '20', '30', '45', '30', '20', '', '-10']),
                'price_usd': appt_prices[appt_type],
            })

    # appointments for a patient that does not exist
    for _ in range(10):
        rows.append({'patient_id': 'P99999', 'provider_name': 'Dr. Lee',
                     'appointment_type': 'Follow-up', 'scheduled_at': '2025-03-01 10:00:00',
                     'status': 'completed', 'duration_minutes': '20', 'price_usd': 79.0})

    appts = pd.DataFrame(rows)
    appts.insert(0, 'appointment_id', [f'A{i:06d}' for i in range(1, len(appts) + 1)])

    duplicates = appts.sample(30, random_state=42)
    return pd.concat([appts, duplicates], ignore_index=True)


def make_lab_results(patients):
    rows = []
    for pid in patients['patient_id'].unique():
        for _ in range(np.random.randint(0, 6)):
            test = np.random.choice(list(lab_tests))
            unit, _, _, low, high = lab_tests[test]
            value = round(np.random.uniform(low, high), 1)
            # a few values that can not be used
            value = np.random.choice([value, 'N/A', '', 'error'], p=[0.92, 0.03, 0.03, 0.02])
            rows.append({
                'patient_id': pid,
                'test_name': test,
                'result_value': value,
                'unit': unit,
                'collected_at': random_dates(start, end, 1)[0].strftime('%Y-%m-%d %H:%M:%S'),
            })

    labs = pd.DataFrame(rows)
    labs.insert(0, 'result_id', [f'L{i:06d}' for i in range(1, len(labs) + 1)])
    return labs


def make_reference_ranges():
    return pd.DataFrame(
        [[test, v[0], v[1], v[2]] for test, v in lab_tests.items()],
        columns=['test_name', 'unit', 'normal_low', 'normal_high']
    )


def main():
    print("Generating raw data...")

    patients = make_patients()
    appointments = make_appointments(patients)
    lab_results = make_lab_results(patients)
    ranges = make_reference_ranges()

    tables = {
        'patients': patients,
        'appointments': appointments,
        'lab_results': lab_results,
        'lab_reference_ranges': ranges,
    }

    for name, df in tables.items():
        df.to_csv(RAW_DIR / f'{name}.csv', index=False)
        print(f"  {name}:", df.shape)


if __name__ == '__main__':
    main()
