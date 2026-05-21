const env = 'local'

const EnvConfig = {
    local: {
        baseApi: 'http://localhost:54321',
    },
    prod: {
        baseApi: 'http://localhost:54321',

    },
}

export default {
    env,
    ...EnvConfig[env]
}
