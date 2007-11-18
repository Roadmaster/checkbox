from hwtest.plugin import Plugin


class ArchitectureInfo(Plugin):

    def register(self, manager):
        super(ArchitectureInfo, self).register(manager)
        self._manager.reactor.call_on("gather", self.gather)

    def gather(self):
        message = self.create_message()
        self._manager.reactor.fire(("report", "architecture"), message)

    def create_message(self):
        return self._manager.registry.dpkg.architecture


factory = ArchitectureInfo
