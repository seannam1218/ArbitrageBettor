import time
import datetime as dt
from fuzzywuzzy import fuzz
import numpy as np
import os



def get_data(session, url, func, request_data, num_tries=10):
    for i in range(num_tries):
        response = func(url, request_data)
        if response.status_code == 200 and len(response.text) > 10:
            return response.json()
        else:
            print(response.status_code, "; trying again...")
            time.sleep(10)
    return -1


def print_json(json, level=0):
    for k, v in json.items():
        print("- "*level, k, end="")
        if type(json[k]) == dict:
            level += 1
            print("")
            print_json(json[k], level)
        elif type(json[k]) == list:
            level += 1
            print(" [")
            for i in json[k]:
                print_json(i, level)
                print(",")
        else:
            print(":", v)
    return


def find_key(json, target_key, level=0):
    # key must be unique. Otherwise, this function grabs the first item with the key.
    ret = None
    for k in json:
        if k == target_key:
            return json[k]
        if type(json[k]) == dict:
            level += 1
            ret = find_key(json[k], target_key, level)
        elif type(json[k]) == list:
            level += 1
            for i in json[k]:
                if find_key(i, target_key, level):
                    ret = find_key(i, target_key, level)
                    break
    if ret == None:
        return -1
    return ret


def resolve_fuzzy_words(dfs, platforms, fuzzy_score_threshold):
    dfs[1]["match_type"] = None

    df_num = 0
    for i, row in dfs[df_num].iterrows():
        if row["join_code"] == None:
            dfs[df_num].at[i, "join_code"] = str(hash(row["event_name" + platforms[df_num].name]))
        find_similar_string(row["event_name" + platforms[df_num].name], dfs[df_num + 1], platforms[df_num + 1].name,
                            "event_name" + platforms[df_num + 1].name, fuzzy_score_threshold,
                            row["join_code"])

    return dfs


def find_similar_string(query, target_df, target_platform_name, target_column, fuzzy_score_threshold, root_join_code):
    choices = np.array(target_df[["index", target_column]])
    candidate = None
    candidate_index = None
    r_total = 0

    competition, _ = query.split(": ")
    team1, team2 = _.split(" +v+ ")

    for i in range(len(choices)):
        c = choices[i][1]
        competition_t, _ = c.split(": ")
        team1_t, team2_t = _.split(" +v+ ")

        if ("women" in competition and "women" not in competition_t) or ("women" in competition_t and "women" not in competition):
            continue

        straight_score_1 = (fuzz.ratio(team1, team1_t) + fuzz.WRatio(team1, team1_t) + fuzz.token_set_ratio(team1, team1_t))/3
        straight_score_2 = (fuzz.ratio(team2, team2_t) + fuzz.WRatio(team2, team2_t) + fuzz.token_set_ratio(team2, team2_t))/3
        cross_score_1 = (fuzz.ratio(team1, team2_t) + fuzz.WRatio(team1, team2_t) + fuzz.token_set_ratio(team1, team2_t))/3
        cross_score_2 = (fuzz.ratio(team2, team1_t) + fuzz.WRatio(team2, team1_t) + fuzz.token_set_ratio(team2, team1_t))/3

        match_type_1 = "1"
        match_type_2 = "2"

        if straight_score_1 > cross_score_1:
            r1 = straight_score_1
            match_type_1 = "straight"
        else:
            r1 = cross_score_1
            match_type_1 = "cross"
        if r1 < fuzzy_score_threshold:
            continue

        if straight_score_2 > cross_score_2:
            r2 = straight_score_2
            match_type_2 = "straight"
        else:
            r2 = cross_score_2
            match_type_2 = "cross"
        if r2 < fuzzy_score_threshold:
            continue

        # if fuzz match for the two teams on two platforms are not the same kind (straight or cross), then stop.
        if match_type_1 != match_type_2:
            continue

        # if competition names of the two events are different, then stop.
        r_competition = (fuzz.ratio(competition, competition_t) + fuzz.WRatio(competition, competition_t) + fuzz.token_set_ratio(competition, competition_t)) / 3
        if r_competition < fuzzy_score_threshold * 0.8:
            continue


        # find entry with maximum ratio score
        new_r_total = r1 + r2 + r_competition
        if new_r_total > r_total:
            r_total = new_r_total
            candidate = [query, c, match_type_1, root_join_code]
            candidate_index = choices[i][0]

    if candidate and target_df.at[candidate_index, "join_code"] == None:
        if root_join_code == None:
            join_code = str(hash(candidate[0]))
        else:
            join_code = root_join_code
        target_df.at[candidate_index, "join_code"] = join_code
        target_df.at[candidate_index, "match_type"] = candidate[2]
    return


def record_analysis_data(top_result, platform_names, path):
    top_result_string = str(top_result["time"].values[0]) + "," + \
                        str(top_result["event_name"+platform_names[0]].values[0]).replace(",", "V") + "," +\
                        str(top_result["event_name"+platform_names[1]].values[0]).replace(",", "V") + "," + \
                        str(top_result["min_margin"].values[0]) + "," +\
                        str(top_result["match_type"].values[0]) + "," + \
                        str(top_result["bet"+platform_names[0]].values[0]) + "," + \
                        str(top_result["bet"+platform_names[1]].values[0]) + "," + \
                        str(top_result["bet_triggered"].values[0]) + "," + \
                        str(top_result["bet_id"+platform_names[0]].values[0]) + "," + \
                        str(top_result["bet_id"+platform_names[1]].values[0]) + \
                        "\n"

    if not os.path.exists(path):
        with open(path, 'w') as file:
            file.write("time,event_name_cloudbet,event_name_thunderpick,min_margin,match_type,bet_cloudbet,bet_thunderpick,bet_triggered,bet_id_cloudbet,bet_id_thunderpick\n")
    with open(path, 'a') as file:
        file.write(top_result_string)
    return


# s1 = "santa clara azores"
# s2 = "vizela"
# print(fuzz.ratio(s1, s2))
# print(fuzz.WRatio(s1, s2))
# print(fuzz.token_set_ratio(s1, s2))