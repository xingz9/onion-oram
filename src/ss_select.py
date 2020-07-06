import random


WORD_BITS = 64
WORD_MASK = (1 << WORD_BITS) - 1


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


class ServerBulkData:

    def __init__(self, bulk_x_vec):
        self.spd_list = []
        max_bits_len = max([bulk_x.bit_length() for bulk_x in bulk_x_vec])

        bulk_x_list = [bulk_x for bulk_x in bulk_x_vec]
        for _ in range(0, max_bits_len, WORD_BITS):
            x_vec = []
            for i in range(len(bulk_x_list)):
                bulk_x = bulk_x_list[i]
                x_vec.append(bulk_x & WORD_MASK)
                bulk_x_list[i] = bulk_x >> WORD_BITS
            self.spd_list.append(ServerPolyData(x_vec))

    def step2(self, comm_list):
        z1 = long(0)
        for i in range(len(self.spd_list)):
            spd = self.spd_list[-i - 1]
            z1 = (z1 << WORD_BITS) ^ spd.step2(comm_list)
        return z1


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
        y_vec[select_index] = WORD_MASK
        cpd = ClientPolyData(y_vec)
        step_result = cpd.step1(beaver_gen)

        z1 = spd.step2(step_result.comm_list)
        z2 = (spd.xor & step_result.u) ^ step_result.v
        print("z1 = 0x{:02x}".format(z1))
        print("z2 = 0x{:02x}".format(z2))
        print("z1 ^ z2 = 0x{:02x}".format(z1 ^ z2))
        print("x[{}]    = 0x{:02x}".format(select_index, x_vec[select_index]))
        print

    bulk_x_vec = [
        278916789189236200707028724350437890037610293376135536604105054872422263555950533467139651898671490218073413238203307964650234633615132740075143722954585,
        59902358990837711399064918643197626906856826678722103104871756680752582570542561400023618845399180858302251442101903572474571277800453247669960685744030,
        5099500265546185964695615655561737363356180182891654803938540187897206131807798342956857242040666894449125886179184706185809738346873960637646854053178631825494933038036015130704849108262931118363097360053411932548744163093428156798420802392925122961294020231006242524052625496525599976366597448311340437354834723749922373440059539810814637174,
    ]
    sbd = ServerBulkData(bulk_x_vec)
    for select_index in range(len(bulk_x_vec)):
        y_vec = [long(0) for _ in range(len(bulk_x_vec))]
        y_vec[select_index] = WORD_MASK
        cpd = ClientPolyData(y_vec)
        step_result = cpd.step1(beaver_gen)

        z1 = sbd.step2(step_result.comm_list)
        print("z1 = 0x{:02x}".format(z1))

        z2 = long(0)
        for i in range(len(sbd.spd_list)):
            spd = sbd.spd_list[-i - 1]
            z2 = (z2 << WORD_BITS)
            z2 ^= (spd.xor & step_result.u) ^ step_result.v
        print("z2 = 0x{:02x}".format(z2))
        print("z1 ^ z2 = 0x{:02x}".format(z1 ^ z2))
        print("x[{}]    = 0x{:02x}".format(select_index, bulk_x_vec[select_index]))
        print
