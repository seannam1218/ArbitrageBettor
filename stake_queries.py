TOURNAMENTS_QUERY = """query SportIndex(
    $sport: String!, 
    $group: String!, 
    $type: SportSearchEnum = all
) 
{
    slugSport(sport: $sport) {
        id,
        name,
        templates(group: $group) {
            id,
            name,
            extId
        },
        categoryList(type: $type, limit: 100) { 
            id, 
            slug, 
            name, 
            fixtureCount(type: $type), 
            tournamentList(type: $type, limit: 100) { 
                id, 
                slug, 
                name,
                fixtureCount(type: $type)
            } 
        }
    }
}
"""


NEW_TOURNAMENTS_QUERY = """query FixtureList(
    $type: SportSearchEnum!, 
    $groups: String!, 
    $offset: Int!, 
    $limit: Int!
) 
{
    fixtureCount(type: $type) 
    fixtureList(type: $type, limit: $limit, offset: $offset) {
        ...FixturePreview
        groups(
            groups: [$groups], 
            status: [active, suspended, deactivated]
        ) {
            ...SportGroupTemplates
        }
    }
}
fragment FixturePreview on SportFixture {
    id
    status
    slug
    marketCount(status: [active, suspended])
    extId
    data {
        __typename
        ...SportFixtureDataMatch
        ...SportFixtureDataOutright
    }
    tournament {
        ...TournamentTreeNested
    }
    eventStatus {
        ...SportFixtureEventStatus
    }
    betradarStream {
        exists
    }
    diceStream {
        exists
    }
    abiosStream {
        exists
        stream {
            id
        }
    }
}
fragment SportFixtureDataMatch on SportFixtureDataMatch {
    startTime
    competitors {
        ...SportFixtureCompetitor
    }
    __typename
}
fragment SportFixtureCompetitor on SportFixtureCompetitor {
    name
    extId
    countryCode
    abbreviation
}
fragment SportFixtureDataOutright on SportFixtureDataOutright {
    name
    startTime
    endTime
    __typename
}
fragment TournamentTreeNested on SportTournament {
    id
    name
    slug
    category {
        ...CategoryTreeNested
    }
}
fragment CategoryTreeNested on SportCategory {
    id
    name
    slug
    sport {
        id
        name
        slug
    }
}
fragment SportFixtureEventStatus on SportFixtureEventStatus {
    homeScore
    awayScore
    matchStatus
    clock {
        matchTime
        remainingTime
    }
    periodScores {
        homeScore
        awayScore
        matchStatus
    }
    currentServer {
        extId
    }
    homeGameScore
    awayGameScore
}
fragment SportGroupTemplates on SportGroup {
    ...SportGroup
    templates(limit: 3, includeEmpty: true) {
        ...SportGroupTemplate
        markets(limit: 1) {
            ...SportMarket
            outcomes {
                ...SportMarketOutcome
            }
        }
    }
}
fragment SportGroup on SportGroup {
    name
    translation
    rank
}
fragment SportGroupTemplate on SportGroupTemplate {
    extId
    rank
    name
}
fragment SportMarket on SportMarket {
    id
    name
    status
    extId
    specifiers
    customBetAvailable
}
fragment SportMarketOutcome on SportMarketOutcome {
    active
    id
    odds
    name
    customBetAvailable
}
"""
# variables:{type:upcoming,groups:winner,limit:10,offset:0}




EVENTS_QUERY = """query TournamentIndex(
    $sport: String!, 
    $category: String!, 
    $tournament: String!, 
    $group: String!, 
    $limit: Int = 50
) 
{
slugTournament(
    sport: $sport, 
    category: $category, 
    tournament: $tournament
) 
{
    id,
    name,
    slug,
    activeFixtureCount: fixtureCount(type: active),
    liveFixtureCount: fixtureCount(type: live),
    popularFixtureCount: fixtureCount(type: popular),
    category {
        id,
        name,
        slug,
        sport {
            id,
            name,
            templates(group: $group) {
                id,
                name,
                extId
            },
            allGroups {
                name,
                translation,
                rank,
                id,
            }
        }
    },
    fixtureList(type: active, limit: $limit) {
        ...FixturePreview,
        groups(
            groups: [$group], 
            status: [active, suspended, deactivated]) {
                ...SportGroupTemplates
            }
        }
    }
},
fragment FixturePreview on SportFixture {
    id,
    status,
    slug,
    marketCount(status: [active, suspended]),
    extId,
    data {
        __typename,
        ...SportFixtureDataMatch,
        ...SportFixtureDataOutright
    },
    tournament {
        ...TournamentTreeNested
    },
    eventStatus {
        ...SportFixtureEventStatus
    }        
},
fragment SportFixtureDataMatch on SportFixtureDataMatch {
    startTime,
    competitors {
        ...SportFixtureCompetitor
    }, 
    __typename
},
fragment SportFixtureCompetitor on SportFixtureCompetitor {
    name, 
    extId, 
    countryCode, 
    abbreviation
},
fragment SportFixtureDataOutright on SportFixtureDataOutright {
    name, 
    startTime, 
    endTime, 
    __typename
}, 
fragment TournamentTreeNested on SportTournament {
    id, 
    name, 
    slug, 
    category {
        ...CategoryTreeNested
    }
}, 
fragment CategoryTreeNested on SportCategory {
    id, 
    name, 
    slug, 
    sport {
        id, 
        name, 
        slug, 
    }
},
fragment SportFixtureEventStatus on SportFixtureEventStatus {
    homeScore,
    awayScore, 
    matchStatus, 
    clock {
        matchTime, 
        remainingTime
    }
},
fragment SportGroupTemplates on SportGroup {
    ...SportGroup, 
    templates(limit: 3, includeEmpty: true) {
        ...SportGroupTemplate, 
        markets(limit: 1) {
            ...SportMarket,
            outcomes {
                ...SportMarketOutcome
            }
        }
    }
},
fragment SportGroup on SportGroup {
    name,
    translation,
    rank
},
fragment SportGroupTemplate on SportGroupTemplate {
    extId, 
    rank, 
    name
}, 
fragment SportMarket on SportMarket {
    id, 
    name, 
    status,
    extId, 
    specifiers, 
    customBetAvailable
},
fragment SportMarketOutcome on SportMarketOutcome {
    active,
    id, 
    odds, 
    name, 
    customBetAvailable
}
"""

USER_BALANCE_QUERY = """query UserBalances {
    user {
        id
        balances {
            available {
                amount
                currency
                __typename
            }
            vault {
                amount
                currency
                __typename
            }
            __typename
        }
        __typename
    }
}"""
# "operationName": "UserBalances"

UPDATE_BASIC_KYC = """mutation UpdateBasicKyc(
    $firstName: String!, 
    $lastName: String!, 
    $birthday: Date!, 
    $phoneNumber: String, 
    $address: String!, 
    $zipCode: String!, 
    $city: String!, 
    $country: CountryEnum!, 
    $occupation: String
) 
{
    updateBasicKyc(
        firstName: $firstName
        lastName: $lastName
        birthday: $birthday
        phoneNumber: $phoneNumber
        address: $address
        zipCode: $zipCode
        city: $city
        country: $country
        occupation: $occupation
    ) 
    {
        id
        __typename
    }
}"""
# "operationName": "UpdateBasicKyc",
# "variables": {
#     "firstName": "Sylvan",
#     "lastName": "Zimmerman",
#     "birthday": "6/16/1982",
#     "address": "Seilerstrasse, 3011 Bern, Switzerland",
#     "zipCode": "3011 Bern",
#     "city": "Bern",
#     "country": "CH",
#     "occupation": "Teacher"}
# }


PLACE_BET_QUERY = """
    mutation SportBetMutation($amount: Float!, $currency: CurrencyEnum!, $outcomeIds: [String!]!) {
      sportBet(
        amount: $amount
        currency: $currency
        outcomeIds: $outcomeIds
        oddsChange: higher
      ) {
        amount
        currency
        outcomes {
          outcome {
            odds
            name
            market {
              name
              specifiers
            }
          }
        }
      }
    }
    """
    # request_data = {
    #     "operationName": "SportBetMutation",
    #     "query": query,
    #     "variables": {
    #         "amount": amount,
    #         "currency": "ltc",
    #         "oddsChange": "higher",
    #         "outcomeIds": [outcome_id],
    #     },
    # }



USER_KYC_INFO_QUERY = """query UserKycInfo {
    user {
        id
        kycStatus
        dob
        createdAt
        isKycBasicRequired
        isKycExtendedRequired
        isKycFullRequired
        isKycUltimateRequired
        hasEmailVerified
        phoneNumber
        hasPhoneNumberVerified
        email
        registeredWithVpn
        isBanned
        isSuspended
        kycBasic {
            ...UserKycBasic
            __typename
        }
        kycExtended {
            ...UserKycExtended
            __typename
        }
        kycFull {
            ...UserKycFull
            __typename
        }
        kycUltimate {
            ...UserKycUltimate
            __typename
        }
        jpyAlternateName: cashierAlternateName(currency: jpy) {
            firstName
            lastName
            __typename
        }
        activeRollovers {
            id
            active
            user {
                id
                __typename
            }
            amount
            lossAmount
            createdAt
            note
            currency
            expectedAmount
            expectedAmountMin
            progress
            activeBets {
                id
                iid
                game {
                    id
                    slug
                    name
                    __typename
                }
                bet {
                    __typename
                }
                __typename
            }
            __typename
        }
        __typename
    }
}
fragment UserKycBasic on UserKycBasic {
    active
    address
    birthday
    city
    country
    createdAt
    firstName
    id
    lastName
    phoneNumber
    rejectedReason
    status
    updatedAt
    zipCode
    occupation
}
fragment UserKycExtended on UserKycExtended {
    id
    active
    createdAt
    id
    rejectedReason
    status
}
fragment UserKycFull on UserKycFull {
    active
    createdAt
    id
    rejectedReason
    status
}
fragment UserKycUltimate on UserKycUltimate {
    id
    active
    createdAt
    id
    rejectedReason
    status
}"""
# "operationName": "UserKycInfo"}
