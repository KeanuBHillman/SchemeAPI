from musicbrainz import get_artist_by_id, get_recording_by_id

recording_id = "02156d29-e70d-45a6-9d35-c1602aa233fc"
artist_id = "38e0beaf-c6ea-4561-808c-ba4a84b66341"


def main():
    response = get_artist_by_id("artist_id")

    print(response)
    print(type(response))


main()
print()
