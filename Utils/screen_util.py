import pandas as pd
from tax_util import get_type


def print_prop_summary(count_new, count_old, total_props, label):
    print(count_old-count_new, 'after', label, 'filtering', round((count_old-count_new)/total_props*100,1), "%")
    return count_new


def mark_screened(df, mask, reason):
    # Flags the rows in mask as screened out: rating = -1 and the reason is added to the comments
    # If a row already has a comment (or was screened for another reason) the reason is appended
    df.loc[mask, 'training_filter'] = False
    df.loc[mask, 'rating'] = -1
    existing = df.loc[mask, 'comments'].fillna('').astype(str)
    df.loc[mask, 'comments'] = existing.where(existing == '', existing + '; ') + reason


def filter_props(df, training=True):
    """
    This is a place to hold all the automatic filtering that I do that can be automated in the future
    Filter                                            | Rating| Comment          | % in 2025 Data
    -----------------------------------------------------------------------------------------------
    acres < 0.075 and landuse in [1180, 6800, 9170]   |   0   | Too small        |  4.7%
    est_bid > 150000                                  |   0   | Too expensive    | 25.8%
    subdiv|address in ["Cliff", "Glassy"], landuse=1180 |   0   | Cliffs           |  1.5%
    landuse in [130, 1171]                            |   0   | MH               |  9.6%
    landuse in [1181, 205]                            |   0   | HOA              |  1.6%
    landuse in [805]                                  |   0   | Cemetery!!!      |  0.0%
    prev_owner is FLC / Forfeited Land Commission     |   0   | FLC              |  n/a
    landuse in [1100, 1101, 9171] and est_bid < 30000 |   0   | Low price house  |  0.6%
    _______________________________________________________________________________________________
                                                                                 | 43.8%
    What's left
    _______________________________________________________________________________________________
    Houses: landuse in [1100, 1101, 9171]                                        | 18.7%
    Land: landuse in [1180, 6800, 1171 (MH w/ land), 9170]                       | 35.3%
    Other: [...,...]                                                             |  1.6%
    _______________________________________________________________________________________________
                                                                                 | 55.6%
    Other filters to put in place...
    -Look for 'HOA' in owners name

    """
    total_props = len(df)
    filterted_props_old = total_props
    print(total_props, "before filtering")
    df['training_filter'] = True
    df['comments'] = df['comments'].astype('object')  # Avoids dtype issues if the column is all NaN
    # Filter out small lots in specific landuse categories
    mark_screened(df, (df['acres'] < 0.075) & (df['land_use'].isin([1180, 6800, 9170])), 'Too small')
    filterted_props_old = print_prop_summary(len(df.loc[df['training_filter']]), filterted_props_old, total_props,
                                              'small land')

    # Filter out very high estimated bid properties
    mark_screened(df, df['est_bid'] > 150000, 'Too expensive')
    filterted_props_old = print_prop_summary(len(df.loc[df['training_filter']]), filterted_props_old, total_props,
                                              'high est bid')

    # Filter out specific subdivisions known to be problematic - the keyword may be in subdiv or address
    cliff_mask = pd.Series(False, index=df.index)
    for column in ['subdiv', 'address']:
        for keyword in ['Cliff', 'Glassy']:
            cliff_mask |= df[column].str.contains(keyword, case=False, na=False)
    mark_screened(df, cliff_mask & (df['land_use'] == 1180), 'Cliffs')
    filterted_props_old = print_prop_summary(len(df.loc[df['training_filter']]), filterted_props_old, total_props,
                                              'Cliffs/Glassy')

    # Filter out mobile homes
    mark_screened(df, df['land_use'].isin([130, 1171]), 'MH')
    filterted_props_old = print_prop_summary(len(df.loc[df['training_filter']]), filterted_props_old, total_props,
                                              'MH')

    # Filter out properties with HOA - either by ownership or landuse
    mark_screened(df, df['land_use'].isin([1181, 205]) | df['owner'].str.contains('HOA', na=False, case=False), 'HOA')
    filterted_props_old = print_prop_summary(len(df.loc[df['training_filter']]), filterted_props_old, total_props,
                                              'HOA')

    # Filter out cemeteries
    mark_screened(df, df['land_use'].isin([805]), 'Cemetery')
    filterted_props_old = print_prop_summary(len(df.loc[df['training_filter']]), filterted_props_old, total_props,
                                              'Creepy Cemeteries')

    # Filter out properties previously owned by the Forfeited Land Commission
    mark_screened(df, df['prev_owner'].str.contains(r'\bFLC\b|FORFEITED\s+LAND', na=False, case=False), 'FLC')
    filterted_props_old = print_prop_summary(len(df.loc[df['training_filter']]), filterted_props_old, total_props,
                                              'Forfeited Land Commission')

    # Filter out very low estimated bid houses
    mark_screened(df, (df['land_use'].isin([1100, 1101, 9171])) & (df['est_bid'] < 30000), 'Low price house')
    filterted_props_old = print_prop_summary(len(df.loc[df['training_filter']]), filterted_props_old, total_props,
                                              'Low Price Houses')

    print("After filtering:", len(df.loc[df['training_filter']]))

    if training:
        return df.loc[df['training_filter']].drop(columns=['training_filter'])
    else:
        return df.drop(columns=['training_filter'])


if __name__ == '__main__':

    training = False
    df = pd.read_csv('Counties/Greenville/props.csv', dtype=get_type())
    # Read bid as a string, but convert to a number - more forgiving than
    df['bid'] = pd.to_numeric(df['bid'].str.replace(',', ''), errors='coerce')  
    # df = filter_props(df, training=training)

    mask = df['land_use'].isin([1171])
    df.loc[mask, 'rating'] = -1.0
    df.loc[mask, 'comments'] = 'MH'

    # df.loc[mask, 'rating'] = float('nan')
    # df.loc[mask, 'comments'] = 'NaN'

    if training:
        df.to_csv('Image_Training/props_screened.csv', index=False, na_rep='NaN')
    else:
        df.to_csv('Counties/Greenville/props.csv', index=False, na_rep='NaN')