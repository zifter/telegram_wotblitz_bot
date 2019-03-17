from Levenshtein import ratio


def search(query, names):
    r = [(ratio(query, name), name) for name in names]
    r = sorted(r, key=lambda v: v[0], reverse=True)

    sr = []
    for v in r[0:5]:
        if v[0] > 0.5:
            sr.append(v[1])
        else:
            break

    return sr