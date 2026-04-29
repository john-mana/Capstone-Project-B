" Seperate traits backend from query_builder right now so I don't mess with any of Johns work :)"

def apply_trait_filters(query, request, Species, Trait, SpeciesTrait):

    trait_name = request.form.get('trait_name')
    trait_value = request.form.get('trait_value')

    if trait_name or trait_value:
        query = query.join(SpeciesTrait, Species.species_id == SpeciesTrait.species_id)\
                     .join(Trait, Trait.trait_id == SpeciesTrait.trait_id)

        if trait_name:
            query = query.filter(Trait.trait_name == trait_name)

        if trait_value:
            query = query.filter(SpeciesTrait.value.ilike(f"%{trait_value}%"))

        query = query.distinct()

    return query
