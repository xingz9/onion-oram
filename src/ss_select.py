import random


class RandomGenerator:

    def __init__(self):
        pass

    def rand_long(self):
        return random.getrandbits(64)


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


if __name__ == '__main__':
    gen = RandomGenerator()
    beaver_gen = BeaverGenerator(gen)

    for _ in range(10):
        x = gen.rand_long()
        y = gen.rand_long()
        print("x  = 0x{:02X}".format(x))
        print("y  = 0x{:02X}".format(y))

        sd = ServerData(x)
        cd = ClientData(y)

        step_result = cd.step1(beaver_gen.gen_beaver_2_share())
        z1 = sd.step2(step_result.comm)
        z2 = (x & step_result.u) ^ step_result.v
        print("z1 = 0x{:02X}".format(z1))
        print("z2 = 0x{:02X}".format(z2))
        print("z1 ^ z2 = 0x{:02X}".format(z1 ^ z2))
        print("x  ^  y = 0x{:02X}".format(x & y))
        print

