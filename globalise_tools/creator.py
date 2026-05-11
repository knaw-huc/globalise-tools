from datetime import datetime

GLOBALISE_TEAM = "https://globalise.huygens.knaw.nl/team/"


class CreatorFactory:
    def __init__(self, script_paths: list[str], commit_id: str):
        self.script_paths = script_paths
        self.commit_id = commit_id

    def creator(self, label: str) -> dict[str, str]:
        ts = datetime.today().isoformat()
        return {
            "type": "DigitalMachineEvent",
            "_label": label,
            "carried_out_by": GLOBALISE_TEAM,
            "timespan": {
                "type": "TimeSpan",
                "end_of_the_begin": ts,
                "begin_of_the_end": ts,
            },
            "used_software_or_firmware": self._used_software_or_firmware()
        }

    def generator(self) -> dict[str, str]:
        return {
            "id": f"https://github.com/knaw-huc/globalise-tools/blob/{self.commit_id}/{self.script_path}",
            "type": "Software",
            "name": self.script_path
        }

    def _used_software_or_firmware(self):
        return [self._software(sp) for sp in self.script_paths]

    def _software(self, script_path: str) -> dict[str, str]:
        return {
            "id": f"https://github.com/knaw-huc/globalise-tools/blob/{self.commit_id}/{script_path}",
            "type": "Software",
            "name": script_path,
        }
