import random


WORD_BITS = 32
WORD_MASK = (1 << WORD_BITS) - 1

LOW_KEY_BITS = 33
HIGH_KEY_BITS = 1
RANDOM_BITS = 30


def gen_rand_bits(bits):
    return random.getrandbits(bits)


def gen_key(low_key_bits=LOW_KEY_BITS, high_key_bits=HIGH_KEY_BITS):
    low_key = gen_rand_bits(low_key_bits - 1) * 2 + 1
    while True:
        high_key = gen_rand_bits(high_key_bits)
        if high_key != 0:
            break
    return low_key + (high_key << low_key_bits)


def gen_select_vector(index, total, key):
    select_vector = [gen_rand_bits(RANDOM_BITS) * key for _ in range(total)]
    select_vector[index] += 1
    return select_vector


class ServerBulkData:

    def __init__(self, bulk_x_vec):
        self.x_vec_list = []
        max_bits_len = max([bulk_x.bit_length() for bulk_x in bulk_x_vec])

        bulk_x_list = [bulk_x for bulk_x in bulk_x_vec]
        for _ in range(0, max_bits_len, WORD_BITS):
            x_vec = []
            for i in range(len(bulk_x_list)):
                bulk_x = bulk_x_list[i]
                x_vec.append(bulk_x & WORD_MASK)
                bulk_x_list[i] = bulk_x >> WORD_BITS
            self.x_vec_list.append(x_vec)

    def select(self, select_vector):
        sum_list = []
        for x_vec in self.x_vec_list:
            assert len(x_vec) == len(select_vector), "{} != {}".format(len(x_vec), len(select_vector))
            prod = [x_vec[i] * select_vector[i] for i in range(len(x_vec))]
            sum_list.append(sum(prod))
        return sum_list


if __name__ == "__main__":
    key = gen_key()
    print("key = 0x{:02x}, len = {}".format(key, key.bit_length()))
    print("")

    n_data = 8
    data_vector = [gen_rand_bits(WORD_BITS) for _ in range(n_data)]
    for i in range(n_data):
        d = data_vector[i]
        print("d[{}] = 0x{:02x}, len = {}".format(i, d, d.bit_length()))
    print("")

    index = 3
    select_vector = gen_select_vector(index, n_data, key)
    for i in range(n_data):
        c = select_vector[i]
        print("s[{}] = 0x{:02x}, len = {}, mod = {}, {}, {}".format(
            i, c, c.bit_length(), (c % key) % 2, (c % (key - 100)) % 2, (c % (key + 200)) % 2
        ))
    print("")

    c_vector = [data_vector[i] * select_vector[i] for i in range(n_data)]
    for i in range(n_data):
        c = c_vector[i]
        print("c[{}] = 0x{:02x}, len = {}".format(i, c, c.bit_length()))
    print("")

    computed_sum = sum(c_vector)
    print("sum = 0x{:02x}, len = {}".format(computed_sum, computed_sum.bit_length()))
    print("sum % key = 0x{:02x}".format(computed_sum % key))
    print("d[{}] = 0x{:02x}".format(index, data_vector[index]))
