from enum import IntEnum, Enum
from functools import cached_property
from typing import Any, Literal
from pydantic import BaseModel, Field, FilePath, PositiveInt, computed_field, field_validator
from mne.channels import DigMontage, make_standard_montage, read_custom_montage, get_builtin_montages as mne_builtins


# ==========================================
# ENUMS
# ==========================================

class LineFrequencyType(IntEnum):
    """Supported power-line frequencies for MNE and BIDS metadata."""

    FIFTY = 50
    SIXTY = 60


class RecordingTypeOpt(Enum):
    CONTINUOUS = "continuous"
    EPOCHED = "epoched"
    DISCONTINUOUS = "discontinuous"


class DatasetType(Enum):
    RAW = "raw"
    DERIVATIVE = "derivative"
    STUDY = "study"

class FilterType(Enum):
    HARDWARE = "hardware"
    SOFTWARE = "software"


class BIDSChanType(Enum):
    """
    Channel types defined by the BIDS specification.

    Upper-case strings used in the 'type' column of BIDS channels.tsv files.
    """

    ACCEL = "ACCEL"
    ADC = "ADC"
    ANGACCEL = "ANGACCEL"
    AUDIO = "AUDIO"
    DAC = "DAC"
    DBS = "DBS"
    ECG = "ECG"
    ECOG = "ECOG"
    EEG = "EEG"
    EMG = "EMG"
    EOG = "EOG"
    EYEGAZE = "EYEGAZE"
    FITERR = "FITERR"
    GSR = "GSR"
    GYRO = "GYRO"
    HEOG = "HEOG"
    HLU = "HLU"
    JNTANG = "JNTANG"
    LATENCY = "LATENCY"
    MAGN = "MAGN"
    MEGGRADAXIAL = "MEGGRADAXIAL"
    MEGGRADPLANAR = "MEGGRADPLANAR"
    MEGMAG = "MEGMAG"
    MEGOTHER = "MEGOTHER"
    MEGREFGRADAXIAL = "MEGREFGRADAXIAL"
    MEGREFGRADPLANAR = "MEGREFGRADPLANAR"
    MEGREFMAG = "MEGREFMAG"
    MISC = "MISC"
    NIRSCWAMPLITUDE = "NIRSCWAMPLITUDE"
    NIRSCWFLUORESCENSEAMPLITUDE = "NIRSCWFLUORESCENSEAMPLITUDE"
    NIRSCWHBO = "NIRSCWHBO"
    NIRSCWHBR = "NIRSCWHBR"
    NIRSCWMUA = "NIRSCWMUA"
    NIRSCWOPTICALDENSITY = "NIRSCWOPTICALDENSITY"
    ORNT = "ORNT"
    OTHER = "OTHER"
    PD = "PD"
    POS = "POS"
    PPG = "PPG"
    PUPIL = "PUPIL"
    REF = "REF"
    RESP = "RESP"
    SEEG = "SEEG"
    SYSCLOCK = "SYSCLOCK"
    TEMP = "TEMP"
    TRIG = "TRIG"
    VEL = "VEL"
    VEOG = "VEOG"


# Dict mapping supplied BIDS chan types to MNE types
bids_to_mne = {
    # Probably a few missing here
    BIDSChanType.EEG: "eeg",
    BIDSChanType.SEEG: "seeg",
    BIDSChanType.ECOG: "ecog",
    BIDSChanType.DBS: "dbs",
    BIDSChanType.REF: "dbs",
    BIDSChanType.VEOG: "eog",
    BIDSChanType.HEOG: "eog",
    BIDSChanType.ECG: "ecg",
    BIDSChanType.EMG: "emg",
    BIDSChanType.PPG: "misc",
    BIDSChanType.GSR: "gsr",
    BIDSChanType.TEMP: "temperature",
    BIDSChanType.AUDIO: "misc",
    BIDSChanType.TRIG: "stim",
}

# ==========================================
# MODELS
# ==========================================
class Dataset(BaseModel):
    """Class for validating dataset_description.json information."""

    Name: str
    DatasetType: str | None = Field(default=None)
    License: str | None = Field(default=None)
    Keywords: list[str] | None = Field(default=None)
    Acknowledgements: str | None = Field(default=None)
    HowToAcknowledge: str | None = Field(default=None)
    Funding: list[str] | None = Field(default=None)
    EthicsApprovals: list[str] | None = Field(default=None)
    ReferencesAndLinks: list[str] | None = Field(default=None)
    DatasetDOI: str | None = Field(default=None)


class SidecarGeneral(BaseModel):
    """Class for validating the general information in the sidecar."""

    # Required fields, explicitly default to "n/a" if missing
    EEGReference: str = Field(default="n/a")
    SamplingFrequency: PositiveInt | Literal["n/a"] = Field(default="n/a")
    PowerLineFrequency: LineFrequencyType | Literal["n/a"] = Field(default="n/a")

    # Not Required fields (Recommended or Optional)
    CapManufacturer: str | None = Field(default=None)
    CapManufacturersModelName: str | None = Field(default=None)
    RecordingType: RecordingTypeOpt | None = Field(default=None)
    EEGGround: str | None = Field(default=None)
    HeadCircumference: PositiveInt | None = Field(default=None)
    EEGPlacementScheme: str | None = Field(default=None)
    SubjectArtefactDescription: str | None = Field(default=None)
    ElectricalStimulation: bool | None = Field(default=None)
    ElectricalStimulationParameters: str | None = Field(default=None)


class SidecarHardware(BaseModel):
    """Class for validating the Hardware information in the sidecar"""

    Manufacturer: str | None = Field(default=None)
    ManufacturersModelName: str | None = Field(default=None)
    SoftwareVersions: str | None = Field(default=None)
    DeviceSerialNumber: str | None = Field(default=None)


class SidecarInstitution(BaseModel):
    """Class for validating the Institution information in the sidecar"""

    InstitutionName: str | None = Field(default=None)
    InstitutionAddress: str | None = Field(default=None)
    InstitutionalDepartmentName: str | None = Field(default=None)


class SidecarTask(BaseModel):
    """Class for validating the Task information in the sidecar"""

    # Required
    TaskName: str

    # Not Required
    TaskDescription: str | None = Field(default=None)
    Instructions: str | None = Field(default=None)
    CogAtlasID: str | None = Field(default=None)
    CogPOID: str | None = Field(default=None)


class Sidecar(BaseModel):
    """High-level class for parsing sidecar-related metadata."""

    # Contains Required fields
    tasks: dict[str, SidecarTask]

    # Contains Required fields, but can create them with 'n/a's
    general: SidecarGeneral = Field(default_factory=SidecarGeneral)

    hardware: SidecarHardware | None = Field(default=None)
    institution: SidecarInstitution | None = Field(default=None)


class Session(BaseModel):
    # This allows coupling sessions with a specific task
    task: str | None = Field(default=None)

    # Should add a check for participant-level (dynamic) task info
    # Maybe here, maybe later

class Run(BaseModel):
    pass


class Filter(BaseModel):
    name: str
    type: FilterType
    info: dict[str, Any]


class AuxChannel(BaseModel):
    bids_type: BIDSChanType = Field(default=BIDSChanType.MISC)
    description: str | None = Field(default=None)
    units: str | None = Field(default=None)
    location: str | dict[str, str] | None = Field(default=None)

    @computed_field
    @property
    def mne_type(self) -> str | None:
        """Generate MNE channel type from BIDS type using mapping provided"""
        return bids_to_mne.get(self.bids_type)


class EEGMontage(BaseModel):
    mne_name: str | None = Field(default=None)
    path: FilePath | None = Field(default=None)

    @field_validator('mne_name', mode="after")
    @classmethod
    def check_mne_name(cls, value: str) -> str | None:
        """Check to see if the mne_name given in the montage is a valid builtin"""
        # Might need to adjust all to lower case for more lenient matching
        if value in mne_builtins():
            return value
        
        return None

    @cached_property
    def montage(self) -> DigMontage | None:
        """Generate a montage if either mne_name or path is present, mne_name takes priority"""
        # Need to check if this is the correct order of resolution
        if self.mne_name:
            return make_standard_montage(self.mne_name)
        elif self.path:
            return read_custom_montage(self.path)
        else:
            return None


class MetadataValidator(BaseModel):
    """Top-level class for Validating the metadata file."""

    dataset: Dataset
    sidecar: Sidecar
    session: dict[str, Session] | None = Field(default=None)
    run: dict[str, Run] | None = Field(default=None)
    aux_chans: dict[str, AuxChannel] | None = Field(default=None)
    events: dict[str, str] | None = Field(default=None)
    filters: list[Filter] | None = Field(default=None)
    eeg_montage: EEGMontage | None = Field(default=None)
