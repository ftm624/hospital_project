import numpy as np
import pandas as pd


def get_provider_profiles(num_staff, provider_profiles_df, providers_wid, *args):
    contacts = np.zeros((num_staff, 24))

    for i in range(0, num_staff+1):
        try:
            contacts[i,:] = provider_profiles_df.loc[providers_wid[i].value,:].values[:24]
        except:
            pass
    return contacts


def provider_number_sparse(num_staff, start_time_wid, end_time_wid, *args):

    providers_ph = np.zeros((num_staff, 24))

    for i in range(0, num_staff):
        z = [0]*24

        start = int(start_time_wid[i].get_interact_value().split(':')[0])
        end = int(end_time_wid[i].get_interact_value().split(':')[0])

        if start<end:
            z[start:end] = [1]*(end-start)
        else:
            z[start:] = [1]*(24-start)
            z[:end] = [1]*end

        providers_ph[i]= z

    return providers_ph



def providers_aligned_shifts(num_staff, provider_profiles_df, providers_wid,  start_time_wid, end_time_wid, *args):
    pp = get_provider_profiles(num_staff, provider_profiles_df, providers_wid, *args)
    num_prov_hour_sparse = provider_number_sparse(num_staff, start_time_wid, end_time_wid, *args)

    for i in range(0, num_staff):
        if sum(num_prov_hour_sparse[i]) != 0:
            if (num_prov_hour_sparse[i][0] == 1.) & (num_prov_hour_sparse[i][-1] == 1.):
                tot = int(sum(num_prov_hour_sparse[i]))
                first_zero = np.argmin(num_prov_hour_sparse[i])
                first_one = np.argmax(num_prov_hour_sparse[i][first_zero:]) + first_zero
                num_prov_hour_sparse[i][first_one:] = pp[i][:24-first_one]
                num_prov_hour_sparse[i][:first_zero] = pp[i][:tot][-first_zero:]

            elif (num_prov_hour_sparse[i][-1] == 1.) & (not (num_prov_hour_sparse[i][0] == 1.)):
                start = np.argmax(num_prov_hour_sparse[i])
                end = start+int(sum(num_prov_hour_sparse[i]))
                num_prov_hour_sparse[i][start:end+1] = pp[i][:end-start] * num_prov_hour_sparse[i][start:end+1]

            else:
                start = np.argmax(num_prov_hour_sparse[i])
                end = start+int(sum(num_prov_hour_sparse[i]))
                num_prov_hour_sparse[i][start:end+1] = pp[i][:end-start+1] * num_prov_hour_sparse[i][start:end+1]

    return num_prov_hour_sparse



def provider_room_cycle_time_aligned(num_staff, providers_wid, provider_profiles_df, start_time_wid, end_time_wid, *args):
    scheduled_providers = []
    providers_room_cycle = np.zeros((num_staff, 24))

    for i in range(0,num_staff):
        scheduled_providers.append(providers_wid[i].get_interact_value())

    total_provider_time = []

    for staffer in scheduled_providers:
        a = provider_profiles_df.loc[staffer]['Average of Arrival to Provider Hrs']
        b = provider_profiles_df.loc[staffer]['Average of Provider to Decision Hrs']
        total_provider_time.append(a + b)

    a = provider_number_sparse(num_staff, start_time_wid, end_time_wid, *args)

    for b in range(0, num_staff):
        providers_room_cycle[b] = np.where(a[b]!=0, total_provider_time[b], 0)

    return providers_room_cycle


def admit_boarding_cycle_time_aligned(num_staff, start_time_wid, end_time_wid, dept_profiles_wid, other_df, admit_boarding_time_wid, *args):
    provider_hour = provider_number_sparse(num_staff, start_time_wid, end_time_wid, *args)
    dept_val = dept_profiles_wid.get_interact_value()
    dept_admit_rate = float(other_df[other['Department Profile'] == dept_val_wid]['Admit Rate'].tolist()[0].split('%')[0])
    dept_admit_dec_depart = other_df[other['Department Profile'] == dept_val_wid]['Admit Decision to Depart'].tolist()[0]
    val = (dept_admit_rate/100) * (admit_boarding_time_wid.get_interact_value() + dept_admit_dec_depart)

    for b in range(0, num_staff):
            provider_hour[b] = np.where(provider_hour[b]!=0, val, 0)

    return provider_hour


def discharge_boarding_cycle_time(num_staff):
    provider_hour = provider_number_sparse(num_staff)
    dept_val = dept_profiles.get_interact_value()
    dept_discharge_rate = 1-((float(other[other['Department Profile'] == dept_val]['Admit Rate'].tolist()[0].split('%')[0]))/100)
    dept_discharge_dec_depart = other[other['Department Profile'] == dept_val]['DC Decision to Depart'].tolist()[0]
    val = dept_discharge_rate * (discharge_boarding_time.get_interact_value() + dept_discharge_dec_depart)

    for b in range(0, num_staff):
            provider_hour[b] = np.where(provider_hour[b]!=0, val, 0)

    return provider_hour



# Admit % x Admit Cycle + Discharge % x Discharge Cycle aligned with shifts
def aa_dd(num_staff):
    p_admit_p = []
    p_discharge_p = []
    for i in range(0, num_staff):
        p = providers[i].get_interact_value()
        p_admit_p.append(provider_profiles['Admit %'].loc[p])
        p_discharge_p.append(provider_profiles['Discharge %'].loc[p])

    pap = np.array([0 if str(x) == 'nan' else x for x in p_admit_p])
    pdp = np.array([1 if str(x) == 'nan' else x for x in p_discharge_p])

    dbst = discharge_boarding_cycle_time(num_staff)
    abcta = admit_boarding_cycle_time_aligned(num_staff)

    return (abcta.T*pap).T + (dbst.T*pdp).T


def total_room_cycle_time(num_staff):
    a = provider_room_cycle_time_aligned(num_staff)
    b = aa_dd(num_staff)
    return a+b


def profiles_decisions_percentage(num_staff):

    p_total_decisions=np.zeros((num_staff,24))

    for i in range(0, num_staff):
        p = providers[i].get_interact_value()
        decisions_per_hour = provider_profiles.loc[p][25:49].values
        total = sum(decisions_per_hour)
        p_total_decisions[i] = decisions_per_hour / total

    return p_total_decisions


def decision_percent_aligned(num_staff):
    pp = profiles_decisions_percentage(num_staff)
    num_prov_hour_sparse = provider_number_sparse(num_staff)

    for i in range(0, num_staff):
        if sum(num_prov_hour_sparse[i]) != 0:
            if (num_prov_hour_sparse[i][0] == 1.) & (num_prov_hour_sparse[i][-1] == 1.):
                tot = int(sum(num_prov_hour_sparse[i]))
                first_zero = np.argmin(num_prov_hour_sparse[i])
                first_one = np.argmax(num_prov_hour_sparse[i][first_zero:]) + first_zero
                num_prov_hour_sparse[i][first_one:] = pp[i][:24-first_one]
                num_prov_hour_sparse[i][:first_zero] = pp[i][:tot][-first_zero:]

            elif (num_prov_hour_sparse[i][-1] == 1.) & (not (num_prov_hour_sparse[i][0] == 1.)):
                start = np.argmax(num_prov_hour_sparse[i])
                end = start+int(sum(num_prov_hour_sparse[i]))
                num_prov_hour_sparse[i][start:end+1] = pp[i][:end-start] * num_prov_hour_sparse[i][start:end+1]

            else:
                start = np.argmax(num_prov_hour_sparse[i])
                end = start+int(sum(num_prov_hour_sparse[i]))
                num_prov_hour_sparse[i][start:end+1] = pp[i][:end-start+1] * num_prov_hour_sparse[i][start:end+1]

    return num_prov_hour_sparse


# Avg Weighted Room Cycle Time
def avg_weighted_room_cycle(num_staff):
    a = total_room_cycle_time(num_staff)
    b = decision_percent_aligned(num_staff)
    return np.sum(a * b, axis=0) / np.sum(b, axis=0)
