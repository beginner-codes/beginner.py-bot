import dippy


class MemberCounterExtension(dippy.Extension):
    client: dippy.Client
    log: dippy.Logging

    def __init__(self):
        super().__init__()
        self._last_count = 0

    @dippy.Extension.listener("ready")
    async def on_ready(self):
        if self._last_count == 0:
            self.log.info("Starting member counter")
            self._update_member_counter()

    def _update_member_counter(self):
        self._schedule_update()
        self._run_update()

    def _run_update(self):
        self.client.loop.create_task(self._do_update())

    def _schedule_update(self):
        self.log.info("Scheduling next member count update")
        self.client.loop.call_later(600, self._run_update)

    async def _do_update(self):
        channel = self.client.get_channel(968972011407826954)
        guild = channel.guild
        members = sum(not member.bot for member in guild.default_role.members)
        self.log.info(f"Updating counter {members:,} {self._last_count:,}")
        if members > self._last_count or members < self._last_count - 20:
            await channel.edit(name=f"📊Members: {members:,}")
            self._last_count = members
