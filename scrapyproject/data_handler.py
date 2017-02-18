import json
import argparse


def main():
    parser = argparse.ArgumentParser(
        description='Cinema booking data extract program.')
    parser.add_argument('--file', type=str, required=True,
                        help='json Lines format file')
    parser.add_argument('--cinema', type=str, required=False,
                        help='target cinema')
    args = parser.parse_args()
    # firgure out movie booking status
    total_booked = 0
    total_seat = 0
    with open(args.file) as f:
        for line in f:
            curr_data = json.loads(line)
            data = curr_data['book_data'].split('/')
            if (args.cinema is not None
                    and curr_data['ciname_name'] != args.cinema):
                continue
            total_booked += int(data[0])
            total_seat += int(data[1])
    title = args.cinema if args.cinema is not None else 'total'
    print("result: {0}: {1}/{2}".format(title, total_booked, total_seat))


if __name__ == '__main__':
    main()
