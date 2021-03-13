class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class UsersList(metaclass=SingletonMeta):
    def __init__(self):
        """
        This is just a singleton dict
        """
        self.users = {}

    def __setitem__(self, key, value):
        self.users[key] = value

    def __getitem__(self, key):
        return self.users[key]

    def __iter__(self):
        return self.users.__iter__()

    def __len__(self):
        return self.users.__len__()

    def __delitem__(self, k):
        return self.users.__delitem__(k)

def test():
    u1=UsersList()
    u1[1] = {'1': 32, 'b': 44, 1: "dfs"}
    print(u1[1])
    u2=UsersList()
    u2[2] = {'2': "If you see this it worked", 'b': 44, 1: "dfs"}
    print(u1[2])
    print("Singleton works" if id(u1)==id(u2) else "singleton not working!")
    for i in u1:
        print(i)

    del u2[2]

if __name__ == "__main__":
    test()

