import random


WORD_BITS = 64


class RandomGenerator:

    def __init__(self):
        pass

    def rand_long(self, bits=WORD_BITS):
        return random.getrandbits(bits)


class BeaverTriple:

    def __init__(self):
        self.a = long(0)
        self.b = long(0)
        self.c = long(0)


class BeaverGenerator:

    def __init__(self, ramdon_gen):
        self.gen = ramdon_gen

    def gen_beaver_2_share(self, b2=None):
        a = self.gen.rand_long()
        b = self.gen.rand_long()
        c = a & b

        t2 = BeaverTriple()
        t2.a = self.gen.rand_long()
        t2.b = self.gen.rand_long() if b2 is None else b2
        t2.c = self.gen.rand_long()

        t1 = BeaverTriple()
        t1.a = a ^ t2.a
        t1.b = b ^ t2.b
        t1.c = c ^ t2.c

        return t1, t2


class CommData:

    def __init__(self):
        self.a1 = long(0)
        self.b1 = long(0)
        self.c1 = long(0)
        self.e2 = long(0)
        self.d = long(0)


class StepResult:

    def __init__(self):
        self.comm = CommData()
        self.u = long(0)
        self.v = long(0)


class ServerData:
    def __init__(self, x):
        self.x = x

    def step2(self, comm):
        x1 = self.x
        x2 = long(0)
        y1 = long(0)
        a1 = comm.a1
        b1 = comm.b1
        c1 = comm.c1
        e1 = x1 ^ a1
        # Don't need d1
        e2 = comm.e2
        # Don't need d2
        e = e1 ^ e2
        d = comm.d
        z1 = c1 ^ (e & b1) ^ (a1 & d) ^ (e & d)
        return z1


class ClientData:
    def __init__(self, y):
        self.y = y

    def step1(self, beavers):
        y1 = 0
        y2 = self.y
        x2 = 0
        a1 = beavers[0].a
        b1 = beavers[0].b
        c1 = beavers[0].c
        a2 = beavers[1].a
        b2 = beavers[1].b
        c2 = beavers[1].c

        # e1: depends on server
        e2 = x2 ^ a2

        d1 = y1 ^ b1
        d2 = y2 ^ b2
        d = d1 ^ d2

        result = StepResult()
        result.comm.a1 = a1
        result.comm.b1 = b1
        result.comm.c1 = c1
        result.comm.e2 = e2
        result.comm.d = d

        # result.u = y ^ b1
        # result.v = a1 ^ y ^ b1 ^ (a2 & b2) ^ c2
        result.u = b2
        result.v = c2 ^ ((a1 ^ a2) & b2) ^ (a2 & d)
        return result


class ServerPolyData:

    def __init__(self, x_vec):
        self.sd = [ServerData(x) for x in x_vec]
        self.xor = x_vec[0]
        for i in range(1, len(x_vec)):
            self.xor ^= x_vec[i]

    def step2(self, comm_list):
        # Check comm_list.size() == sd.size()
        result = long(0)
        for i in range(len(self.sd)):
            result ^= self.sd[i].step2(comm_list[i])
        return result


class PolyStepResult:

    def __init__(self):
        self.comm_list = []
        self.u = long(0)
        self.v = long(0)


class ClientPolyData:

    def __init__(self, y_vec):
        self.cd = [ClientData(y) for y in y_vec]

    def step1(self, beaver_gen):
        result = PolyStepResult()

        triple = beaver_gen.gen_beaver_2_share()
        b2 = triple[1].b
        step_result = self.cd[0].step1(triple)
        result.comm_list.append(step_result.comm)
        result.u = step_result.u
        result.v = step_result.v

        for i in range(1, len(self.cd)):
            step_result = self.cd[i].step1(beaver_gen.gen_beaver_2_share(b2))
            result.comm_list.append(step_result.comm)
            # Check result.u == step_result.u
            result.v ^= step_result.v

        return result


if __name__ == '__main__':
    gen = RandomGenerator()
    beaver_gen = BeaverGenerator(gen)

    for _ in range(10):
        x = gen.rand_long()
        y = gen.rand_long()
        print("x  = 0x{:02x}".format(x))
        print("y  = 0x{:02x}".format(y))

        sd = ServerData(x)
        cd = ClientData(y)

        step_result = cd.step1(beaver_gen.gen_beaver_2_share())
        z1 = sd.step2(step_result.comm)
        z2 = (x & step_result.u) ^ step_result.v
        print("z1 = 0x{:02x}".format(z1))
        print("z2 = 0x{:02x}".format(z2))
        print("z1 ^ z2 = 0x{:02x}".format(z1 ^ z2))
        print("x  ^  y = 0x{:02x}".format(x & y))
        print

        x_vec = [i + 1 for i in range(5)]
        spd = ServerPolyData(x_vec)
        for select_index in range(len(x_vec)):
            y_vec = [long(0) for _ in range(len(x_vec))]
            y_vec[select_index] = (1 << WORD_BITS) - 1
            cpd = ClientPolyData(y_vec)
            step_result = cpd.step1(beaver_gen)

            z1 = spd.step2(step_result.comm_list)
            z2 = (spd.xor & step_result.u) ^ step_result.v
            print("z1 = 0x{:02x}".format(z1))
            print("z2 = 0x{:02x}".format(z2))
            print("z1 ^ z2 = 0x{:02x}".format(z1 ^ z2))
            print("x[{}] = 0x{:02x}".format(select_index, x_vec[select_index]))
